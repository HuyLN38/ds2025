# client.py
import socket
import os


class FileTransferClient:
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.socket = None

    def list_files(self) -> bool:
        """Request list of available files from server"""
        self.connect()
        try:
            # Send operation type
            self.socket.send(b'LIST')
            response = self.socket.recv(1024)  # Wait for acknowledgment
            if response != b'OK':
                print("Server rejected operation")
                return False

            # Receive file list size
            list_size = int(self.socket.recv(1024).decode())
            self.socket.send(b'OK')  # Acknowledge size

            # Receive file list
            data = self.socket.recv(list_size).decode()
            print("\nAvailable files on server:")
            print("-" * 50)
            for file_info in data.split('\n'):
                if file_info:  # Skip empty lines
                    print(file_info)
            print("-" * 50)
            return True

        except Exception as e:
            print(f"Error listing files: {e}")
            return False
        finally:
            self.socket.close()

    def connect(self) -> None:
        """Establish connection to server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    def send_file(self, filename: str, save_as: str = None) -> bool:
        """Send a file to the server"""
        if not os.path.exists(filename):
            print(f"Error: File {filename} not found")
            return False

        self.connect()
        try:
            # Send operation type
            self.socket.send(b'SEND')
            response = self.socket.recv(1024)  # Wait for acknowledgment
            if response != b'OK':
                print("Server rejected operation")
                return False

            # Send filename
            self.socket.send(filename.encode())
            response = self.socket.recv(1024)  # Wait for acknowledgment
            if response != b'OK':
                print("Server rejected filename")
                return False

            # Send file size
            file_size = os.path.getsize(filename)
            self.socket.send(str(file_size).encode())
            response = self.socket.recv(1024)  # Wait for acknowledgment
            if response != b'OK':
                print("Server rejected file size")
                return False

            # Send file data
            bytes_sent = 0
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.socket.send(data)
                    bytes_sent += len(data)
                    progress = (bytes_sent / file_size) * 100
                    print(f"Progress: {progress:.1f}%", end='\r')

            print(f"\nFile {filename} sent successfully")
            return True

        except Exception as e:
            print(f"Error during file transfer: {e}")
            return False
        finally:
            self.socket.close()

    def request_file(self, filename: str, save_as: str = None) -> bool:
        """Request and receive a file from the server"""
        self.connect()
        try:
            # Send operation type
            self.socket.send(b'REQUEST')
            response = self.socket.recv(1024)  # Wait for acknowledgment
            if response != b'OK':
                print("Server rejected operation")
                return False

            # Send filename
            self.socket.send(filename.encode())

            # Receive initial response
            response = self.socket.recv(1024)
            if response == b'FILE_NOT_FOUND':
                print(f"Error: File {filename} not found on server")
                return False
            elif response == b'OK':
                # Receive file size
                file_size_data = self.socket.recv(1024)
                file_size = int(file_size_data.decode())
                self.socket.send(b'OK')  # Acknowledge file size
                print(f"File size: {file_size} bytes")

                # Receive file data
                received_data = b''
                while len(received_data) < file_size:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    received_data += data
                    progress = (len(received_data) / file_size) * 100
                    print(f"Progress: {progress:.1f}%", end='\r')

                # Save file
                save_path = save_as or f"received_{filename}"
                with open(save_path, 'wb') as f:
                    f.write(received_data)
                print(f"\nFile saved as {save_path}")
                return True
            else:
                print("Unexpected server response")
                return False

        except Exception as e:
            print(f"Error during file transfer: {e}")
            return False
        finally:
            if self.socket:
                self.socket.close()
