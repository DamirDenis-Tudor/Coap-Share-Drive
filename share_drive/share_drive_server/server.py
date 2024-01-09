import argparse
import os
import queue
from multiprocessing import Process, Queue
from select import select
from socket import socket, AF_INET, SOCK_DGRAM
from time import sleep
from pyfiglet import Figlet

from coap_core.coap_utilities.coap_logger import logger, LogColor
from coap_core.coap_worker.coap_worker_pool import CoapWorkerPool
from share_drive.share_drive_server.server_resource import ServerResource


def clean_terminal():
    """
    Clears the terminal screen and prints the CoAP Drive Server title using Figlet.
    """
    os.system('clear')
    logger.debug(Figlet(font="standard", width=400).renderText("Coap Drive Server"), color=LogColor.BLUE, stamp=False)


class Server:
    def __init__(self, ip_address, port):
        """
        Initializes the CoAP server with the given IP address and port.

        Args:
            ip_address (str): The IP address to bind the server socket.
            port (int): The port number to bind the server socket.
        """
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind((ip_address, port))

        # Creating a ServerResource instance for handling CoAP requests
        self._resource = ServerResource("share_drive", f"{os.path.expanduser('~')}/coap/server/resources/")

        # Dictionary to store data queues and client processes for each address
        self._processes_queues = {}

        # Queue for receiving incoming CoAP messages
        self._recv_queue = queue.Queue()

        # Enabling debug mode for the CoAP logger
        logger.debug_mode = True
        # Clearing the terminal and printing the CoAP Drive Server title
        clean_terminal()

    @logger
    def listen(self):
        """
        Listens for incoming CoAP messages and manages client processes.

        This method continuously listens for incoming CoAP messages on the server socket.
        It utilizes a multiprocessing approach to handle each client in a separate process,
        allowing for concurrent communication with multiple clients.

        The server maintains a dictionary (`self._processes_queues`) to store data queues and
        client processes for each unique client address. Each client's CoAPWorkerPool runs
        in a separate process to provide parallel processing of requests.

        Raises:
            Exception: If an error occurs during execution.
        """
        try:
            while True:
                # Using select to check if the server socket has incoming data
                active_socket, _, _ = select([self._skt], [], [], 1)

                if active_socket:
                    # Receiving data and address from the socket
                    data, address = self._skt.recvfrom(1152)
                    # Putting the received data and address into the queue
                    self._recv_queue.put((data, address))

                    # Checking if there is an existing process for the client address
                    if address not in self._processes_queues:
                        # Creating a new data queue and CoapWorkerPool for the client
                        data_queue = Queue()
                        pool = CoapWorkerPool(self._skt, self._resource, data_queue)
                        client_process = Process(target=pool.start)
                        client_process.start()

                        # Storing the data queue and client process in the dictionary
                        self._processes_queues[address] = data_queue, client_process
                        logger.debug(f"Creating a new process {client_process} for {address}.", LogColor.CYAN)
                        sleep(0.5)

                    # Putting the received data and address into the client's data queue
                    self._processes_queues[address][0].put((data, address))

        except Exception as e:
            # Terminating and joining all client processes in case of an exception
            for _, process in self._processes_queues.values():
                process[1].terminate()
                process[1].join()
            raise e


def main():
    """
    Main function to parse command-line arguments and start the CoAP server.
    """
    parser = argparse.ArgumentParser(description='Server script with address and port arguments')

    parser.add_argument('--server_address', type=str, default='127.0.0.1', help='Server address')
    parser.add_argument('--server_port', type=int, default=5683, help='Server port')

    args = parser.parse_args()

    # Creating and starting the CoAP server
    Server(args.server_address, args.server_port).listen()


# Entry point for the script
if __name__ == "__main__":
    main()
