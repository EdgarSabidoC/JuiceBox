import docker
import time

client = docker.from_env()

while True:
    containers = client.containers.list()
    if len(containers) > 0:
        for container in containers:
            stats = container.stats(stream=False)
            name = container.name
            cpu = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            mem = stats["memory_stats"]["usage"]
            print(f"{name} | CPU: {cpu} | MEM: {mem}")
            time.sleep(2)
