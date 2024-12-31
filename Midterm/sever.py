from redis import RedisClone
from rpc import RPCServer

server = RPCServer('127.0.0.1', 8080)
redis_instance = RedisClone()
server.registerInstance(redis_instance)
server.run()
