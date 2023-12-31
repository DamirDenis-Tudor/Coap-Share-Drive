# 1. Sequence diagram + Packet format

![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/f8f02abe-3f49-40bb-9ce2-04ad12cd9f60)

# 2. Class Diagram

![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/3deef87f-eaa9-4102-b07d-13d494e6d335)

# 3. Tests
### Test with a window of 10000 packets for a 400MB+ file
![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/ae72906f-c1c5-41aa-99fd-4052c310f264)

### Test with a window of 1000 packets for a 400MB+ file
![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/c5c11f29-fdd9-4f61-83d7-d7abfd64c9cc)

### Test with a window of 100 packets for a 400MB+ file
![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/a518b73d-c1be-49f1-b0d0-f0c24a83b73c)

# 4. CoAP Message Format

### Client IP
- Field wrapped when the packet is recieved.

### Packet Types
- **Confirmable (CON - 00)**: Used for request messages expecting acknowledgments.
- **Non-Confirmable (NON - 01)**: For one-way messages not requiring acknowledgments.
- **Acknowledgment (ACK - 10)**: Acknowledgment for Confirmable messages.
- **Reset (RST - 11)**: Used to reject unprocessable messages.

### Token Length
- Variable length for the TOKEN field.

### Packet Code
- Message codes follow the format 'c.dd' to specify request or response type.

  ### Request Codes
  - Used in client-initiated CoAP requests.
    - **GET (0.01)**: Retrieve a resource.
    - **POST (0.02)**: Create or update a resource.
    - **PUT (0.03)**: Update or create a resource.
    - **DELETE (0.04)**: Delete a resource.
    - **Other methods (0.05 to 0.31)**: Custom request methods can be defined.

  ### Success Response Codes
  - Used in CoAP responses for successful operations.
    - **2.01 Created**: Resource creation successful.
    - **2.02 Deleted**: Resource deletion successful.
    - **2.03 Valid**: Resource is valid, use cached version.
    - **2.04 Changed**: Resource update successful.
    - **2.05 Content**: Response contains the requested resource representation.

  ### Client Error Response Codes
  - Indicate errors on the client side.
    - **4.00 Bad Request**: Malformed request.
    - **4.01 Unauthorized**: Client authentication required.
    - **4.04 Not Found**: Requested resource not found.
    - **4.05 Method Not Allowed**: Method not allowed for the resource.
    - **4.08 Request Entity Too Large**: Request payload is too large.

  ### Server Error Response Codes
  - Indicate errors on the server side.
    - **5.00 Internal Server Error**: Internal server error.
    - **5.01 Not Implemented**: Server doesn't support the requested functionality.
    - **5.03 Service Unavailable**: Service is temporarily unavailable.

### Packet ID
- Identifier to detect duplicates.

### Token 
- Identifier to group packets by response/request.
