# 1. Component diagram
### Description ...
![image](arhitecture/photos/component_diagram.png)

# 2. Sequence Diagram
### Description ...
![image](arhitecture/photos/sequence_diagram.png)

# 3. Class Diagram
### Description ...
![image](arhitecture/photos/class_diagram.png)

# 4. CoAP Packet Format
### Description ... to be updated
![image](arhitecture/photos/packet_format.png)

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
