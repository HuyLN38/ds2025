# server.py
import socket
import os
from typing import Tuple


class FileTransferServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None
        self.local_ip = self.get_local_ip()

    def get_local_ip(self) -> str:
        """Get the local IP address of the machine"""
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return ip
        except Exception:
            return '127.0.0.1'

    def setup_socket(self) -> None:
        """Initialize and configure the server socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"Server listening on all interfaces")
        print(f"Connect to this server using IP: {self.local_ip} and port: {self.port}")

    def accept_connection(self) -> Tuple[socket.socket, Tuple]:
        """Accept incoming connection"""
        client_socket, address = self.socket.accept()
        print(f"Connection from {address}")
        return client_socket, address

    def handle_file_transfer(self, client_socket: socket.socket) -> None:
        """Handle the file transfer process"""
        try:
            # Receive operation type
            operation = client_socket.recv(1024)
            client_socket.send(b'OK')  # Acknowledge operation

            if operation == b'SEND':
                self.receive_file(client_socket)
            elif operation == b'REQUEST':
                self.send_file(client_socket)
            elif operation == b'LIST':
                self.send_file_list(client_socket)
            else:
                print(f"Unknown operation: {operation}")
        finally:
            client_socket.close()

    def send_file_list(self, client_socket: socket.socket) -> None:
        """Send list of available files to client"""
        try:
            # Get list of files in current directory with sizes
            file_list = []
            for filename in os.listdir('.'):
                if os.path.isfile(filename):  # Only list files, not directories
                    size = os.path.getsize(filename)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    file_list.append(f"{filename:<30} {size_str:>10}")

            # Convert list to string
            file_list_str = '\n'.join(file_list)
            encoded_list = file_list_str.encode()

            # Send size of file list
            client_socket.send(str(len(encoded_list)).encode())
            response = client_socket.recv(1024)  # Wait for acknowledgment

            if response == b'OK':
                # Send the file list
                client_socket.send(encoded_list)
                print("File list sent successfully")
            else:
                print("Client rejected file list size")

        except Exception as e:
            print(f"Error sending file list: {e}")

        except Exception as e:
            print(f"Error during file transfer: {e}")
        finally:
            client_socket.close()

    def receive_file(self, client_socket: socket.socket) -> None:
        """Handle receiving a file from client"""
        try:
            # Receive filename
            filename = client_socket.recv(1024).decode()
            client_socket.send(b'OK')  # Acknowledge filename

            # Receive file size
            file_size = int(client_socket.recv(1024).decode())
            client_socket.send(b'OK')  # Acknowledge file size
            print(f"Receiving file: {filename} ({file_size} bytes)")

            # Receive file data
            received_data = b''
            while len(received_data) < file_size:
                data = client_socket.recv(4096)
                if not data:
                    break
                received_data += data
                progress = (len(received_data) / file_size) * 100
                print(f"Progress: {progress:.1f}%", end='\r')

            # Save file
            with open(filename, 'wb') as f:
                f.write(received_data)
            print(f"\nFile {filename} received successfully")

        except Exception as e:
            print(f"Error receiving file: {e}")

    def send_file(self, client_socket: socket.socket) -> None:
        """Handle sending a file to client"""
        try:
            # Receive filename request
            filename = client_socket.recv(1024).decode()
            print(f"Requested file: {filename}")

            if os.path.exists(filename):
                client_socket.send(b'OK')

                # Send file size
                file_size = os.path.getsize(filename)
                client_socket.send(str(file_size).encode())
                response = client_socket.recv(1024)  # Wait for acknowledgment

                if response == b'OK':
                    # Send file data
                    bytes_sent = 0
                    with open(filename, 'rb') as f:
                        while True:
                            data = f.read(4096)
                            if not data:
                                break
                            client_socket.send(data)
                            bytes_sent += len(data)
                            progress = (bytes_sent / file_size) * 100
                            print(f"Progress: {progress:.1f}%", end='\r')
                    print(f"\nFile {filename} sent successfully")
                else:
                    print("Client rejected file size")
            else:
                client_socket.send(b'FILE_NOT_FOUND')
                print(f"File {filename} not found")

        except Exception as e:
            print(f"Error sending file: {e}")

    def run(self) -> None:
        """Run the server"""
        self.setup_socket()
        try:
            while True:
                client_socket, _ = self.accept_connection()
                self.handle_file_transfer(client_socket)
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            if self.socket:
                self.socket.close()