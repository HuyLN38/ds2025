from rpc import RPCClient

def main():
    print("Redis Clone Client")
    print("Type your commands (e.g., `SET key value`) or type `EXIT` to quit.")

    client = RPCClient('127.0.0.1', 8080)
    client.connect()

    try:
        while True:
            command = input("> ").strip()
            if command.lower() == "exit":
                print("Goodbye!")
                break

            parts = command.split()
            if not parts:
                continue

            cmd, *args = parts
            cmd = cmd.lower()

            if cmd == "del":
                cmd = "delete"

            try:
                if cmd in ["set", "get", "delete", "append", "keys", "flushall"]:
                    method = getattr(client, cmd)
                    result = method(*args)
                    print(result)
                else:
                    print("Unknown command.")
            except Exception as e:
                print(f"Error: {str(e)}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
