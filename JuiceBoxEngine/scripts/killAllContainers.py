#!/usr/bin/env python3
import time, docker

if __name__ == "__main__":
    # Para y destruye todos los contenedores existentes:
    client = docker.from_env()
    for container in client.containers.list(all=True):
        container.stop()
        container.remove()
