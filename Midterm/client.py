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
                if cmd in ["set", "get", "delete", "append", "keys", "flushall", 
                          "expire", "ttl", "persist", "exists", 
                          ]:
                    if cmd == "set" and len(args) >= 4 and args[-2].lower() == "ex":
                        key, value = args[0], args[1]
                        ex = int(args[-1])
                        result = client.set(key, value, ex=ex)
                    else:
                        method = getattr(client, cmd)
                        result = method(*args)

                    # Handle special TTL cases
                    if cmd == "ttl":
                        if result == -2:
                            result= "Key does not exist."
                        elif result == -1:
                            result="Key exists but has no expiration."
                        
                    print(result)
                else:
                    print("Unknown command.")
            except Exception as e:
                print(f"Error: {str(e)}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

