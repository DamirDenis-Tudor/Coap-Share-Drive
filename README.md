# 1. Sequence digram

![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/95768d98-59f4-4a45-a3ad-1f644f7d76a8)


# 2. CoAP Message Format

![image](https://github.com/TUIASI-AC-IoT/proiectrcp2023-echipa-21-2023/assets/101417927/b7c8d616-c615-412d-89b8-31e86f128b9a)

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

### Format Length 
- Value for Packet Depth, File Format, Total Packets.

### Packet Depth
- Represents packet depth within folders.

### File Format
- Code identifier for supported file extensions, sent with the last packet.

### Total Packets
- Total number of expected packets, sent with the first packet.

### Payload
- Packet content (path, raw bytes, etc.).


