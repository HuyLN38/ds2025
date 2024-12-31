from rpc import RPCServer

class RedisClone:
    def __init__(self):
        self.data_store = {}  # Dictionary to store key-value pairs

    # SET key value
    def set(self, key, value):
        self.data_store[key] = value
        return f"OK"

    # GET key
    def get(self, key):
        return self.data_store.get(key, None)

    # DEL key
    def delete(self, key):
        return self.data_store.pop(key, None)

    # KEYS
    def keys(self):
        return list(self.data_store.keys())

    # FLUSHALL
    def flushall(self):
        self.data_store.clear()
        return "OK"

    # Append to a string
    def append(self, key, value):
        if key in self.data_store and isinstance(self.data_store[key], str):
            self.data_store[key] += value
            return len(self.data_store[key])
        else:
            return "Key does not exist or value is not a string."
