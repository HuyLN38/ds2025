from xmlrpc.server import SimpleXMLRPCServer
import os

def upload_file(filename, file_data):
    """
    Save the uploaded file to the current directory.
    """
    try:
        with open(filename, "wb") as f:
            f.write(file_data.data)
        print(f"File '{filename}' received successfully.")
        return f"File '{filename}' uploaded successfully."
    except Exception as e:
        return f"Failed to upload file: {str(e)}"

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 9000
    server = SimpleXMLRPCServer((host, port))
    print(f"RPC server is running on {host}:{port}")
    server.register_function(upload_file, "upload_file")
    server.serve_forever()