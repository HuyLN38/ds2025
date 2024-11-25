from client import FileTransferClient
from server import FileTransferServer

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='TCP File Transfer')
    parser.add_argument('--mode', choices=['server', 'client'], help='Run as server or client')
    parser.add_argument('--ip', '-i', default='localhost', help='IP address for client to connect to')
    parser.add_argument('--port', '-p', type=int, default=12345, help='Port number')
    parser.add_argument('--fn', nargs='?', help='File to transfer (client mode only)')
    parser.add_argument('--sor', choices=['send', 'receive', 'list'],
                        help='Send, receive, or list files (client mode only)')
    parser.add_argument('--save-as', '-s', help='Save file with different name')

    args = parser.parse_args()

    print("Choose the mode: server or client")
    print("1. Server")
    print("2. Client")
    mode = input("Enter the mode: ")
    if mode == "1":
        args.mode = "server"
    elif mode == "2":
        args.mode = "client"

        print("Enter the IP address : ", end="")
        ip = input()
        args.ip = ip

        print("Enter send or receive or list : ", end="")
        sor = input()
        args.sor = sor

    else:
        print("Invalid mode")
        exit()



    if args.mode == "server":
        server = FileTransferServer(port=args.port)
        server.run()
    elif args.mode == "client":
        if not args.sor:
            parser.error("Client mode requires --sor option (send, receive, or list)")

        client = FileTransferClient(host=args.ip, port=args.port)
        if args.sor == 'list':
            client.list_files()
        else:
            if not args.fn:
                parser.error("Filename required for send/receive operations")
            if args.sor == 'send':
                client.send_file(args.fn, args.save_as)
            elif args.sor == 'receive':
                client.request_file(args.fn, args.save_as)