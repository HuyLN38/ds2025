import os

import xmlrpc.client

def send_file(filename, host='127.0.0.1', port=9000):
    if not os.path.exists(filename):
        print(f"File {filename} does not exist.")
        return

    with open(filename, "rb") as f:
        file_data = f.read()

    proxy = xmlrpc.client.ServerProxy(f"http://{host}:{port}/")
    print(f"Connected to RPC server at {host}:{port}")
    try:
        response = proxy.upload_file(os.path.basename(filename), xmlrpc.client.Binary(file_data))
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    filename = input("Enter the filename to send: ")
    send_file("meow.jpg")