import os
import redis
from rq import Worker, Queue, Connection

listen = ["high", "default", "low"]

redis_url = os.getenv("REDIS_URL", "redis://redis")
conn = redis.from_url(redis_url)


if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
