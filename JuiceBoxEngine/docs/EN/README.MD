# JUICE BOX ENGINE
This app runs on a **host/server** machine.

The communication is based on **events** or **signals** through a custom Unix Domain Socket.

- **JuiceBox_TUI:** Text User Interface for admins written in Python with Textual.
- **JuiceShop_Client:** graphic user interface for users based on a webapp.
- **JuiceShop_API:** REST API which connect the JuiceShop_Client with the Juice Box Engine (written in Go.

### Message structure for the Juice Box Engine's API:
    {
      "prog": ("JS" | "RTB"),
      "command": <string>,
      [ "args": { ("port": <integer> | "name": <string> ) } ]
    }

- ***prog:*** It uses `"JS"` (Juice Shop) or `"RTB"` (Root The Box) to choose which program would be used.
- ***command:*** Command string, written in capital letters with `"__"` as preffix and suffix, e.g.: `__START_CONTAINER__`.
- ***args:*** Arguments for the command, here you must add a port or name to specify the container.

## Root The Box

### Start the service:
Command: `__START__`.

### Restart the service:
Command: `__RESTART__`.

### Stop the service:
Command: `__KILL__`.

**NOTE:** *Destroys **ALL** containers related to Root The Box.*

### Check the service status:
Command: `__STATUS__`

### Configure the service:
Command: `__CONFIG__`

Modifies the file at `JuiceBoxEngine/configs/rootTheBox.json`.

## OWASP Juice Shop

### Start the service:
Command: `__START_CONTAINER__`.

<h3 id="js-restart-the-sevice">Restart the service:</h3>

Command: `__RESTART__`.

**NOTE:** *All Juice Shop containers will be stopped and destroyed at restart (it uses internally the command `__KILL_ALL__`).*

[`See: Stop ALL the containers`](#stop-all-the-containers)

### Stop a specific container:
Command:  `__KILL_CONTAINER__`

Args: (`port` | `name`)

### Stop **ALL** the containers:
Command: `__KILL_ALL__`

### Check the service status:
Command: `__STATUS__`

### Configure the service:
Command: `__CONFIG__`

Modifies the file at `JuiceBoxEngine/configs/juiceShop.json`

**NOTE:** *All changes made on the configuration files will only take effect upon restart. Since all Juice Shop containers depend on the same **ctf_key**, executing this command will destroy all containers to mantain engine cohesion and consistency.* [`See: Restart the service`](#js-restart-the-sevice)

### Generate the XML configuration file for Root The Box (missions/challenges from Juice Shop):
Command: `__GENERATE_XML__`

**NOTE:** *Internally uses the command `__RESET__`.* [`See: Restart the service`](#js-restart-the-sevice)

## NOTES
- Scripts require Python v. 3.9+ which allows typing without importing the typing package.
- Due the nature of Docker containers, when a container is stopped it will alse be destroyed.
- If you want to persist the data, create a volume between the desired container and the host.
- By default, the containers can communicate between them through the default Docker network.
- For a better control on containers communication create specific custom networks.