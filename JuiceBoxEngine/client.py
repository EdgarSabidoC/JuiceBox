import socket, time, json
from typing import Optional, Union

SOCKET_PATH = "/tmp/juiceboxengine.sock"


def send_command(
    prog: str, command: str, args: Optional[dict[str, Union[str, int]]] = None
) -> str:
    message: dict[str, Union[str, dict[str, Union[str, int]]]] = {
        "prog": prog,
        "command": command,
    }
    if args is not None:
        message["args"] = args

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)  # Se abre la conexión con el socket
            client.sendall(json.dumps(message).encode())
            response = client.recv(4096).decode()
            client.close()  # Se cierra la conexión con el socket
            return response
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# Ejemplos de uso
if __name__ == "__main__":
    # Se reinicia RootTheBox
    # print(send_command("RTB", "__RESTART__"))
    # print(send_command("RTB", "__KILL__"))
    # # Iniciar RootTheBox
    # print(send_command("RTB", "__START__"))
    print(send_command("RTB", "__STATUS__"))

    # # Iniciar un contenedor de Juice Shop
    # print(send_command("JS", "__START_CONTAINER__"))

    # # Iniciar un contenedor de Juice Shop
    # print(send_command("JS", "__STATUS__", {"port": 3000}))

    # # Detener contenedor por nombre
    # print(send_command("JS", "__KILL_CONTAINER__", {"port": 3000}))
