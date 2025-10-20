![](https://img.shields.io/badge/python-3.8+-blue.svg)
![](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)
# Fogbed

Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtualized environments using a desktop or distributed approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

# Install

You can install Fogbed directly from the GitHub repository in a single step by using the following command:

`wget https://raw.githubusercontent.com/larsid/fogbed/main/install-fogbed.sh && chmod +x install-fogbed.sh && sudo ./install-fogbed.sh`

The `install-fogbed.sh` script automates the installation of the Fogbed tool and its dependencies on Ubuntu-based Linux systems. This command uses `wget` to retrieve the script from the main branch and saves it to the current directory as `install-fogbed.sh`. Then, it uses chmod (change mode) to add execute permissions to the installation script. The `+x` flag grants execution rights, allowing the script to be run as a program rather than just being read as a text file. Finally, it executes the installation script with superuser privileges using `sudo`, where the `./` prefix indicates that the script is located in the current directory. Administrator privileges are required because the script needs to install system packages, create directories in `/opt`, and configure system services. Below, we detail the steps executed by the installation script.

## Installation Steps

The Fogbed installation script was tested only on Ubuntu 24.04. If you are facing errors while installing on a different system, or if you wish to modify the proposed configuration, you can review the steps performed by the script. The installation process is divided into the following stages:

### 1. System Dependencies Installation

The script begins by updating the system package list and installing essential dependencies through `apt-get`. The installed packages include:

- **Network Tools:** `net-tools`, `iproute2`, `iputils-ping`, `tcpdump`, `iperf`.
- **Development Tools:** `python3`, `python3-pip`, `git`, `curl`, `ansible`.
- **Python Virtual Environment:** The `python3.x-venv` package corresponding to the installed Python version.

### 2. Working Directory Setup

A working directory is created at `/opt/fogbed`. If an existing directory is found, it is removed to ensure a clean installation.

### 3. Containernet Installation

The script clones the [Containernet](https://github.com/containernet/containernet) repository to the `/opt/fogbed/containernet` directory and then uses an Ansible playbook to install Containernet and its system dependencies, which include Docker, Mininet, and Open vSwitch.

### 4. Fogbed and Containernet Installation in Virtual Environment

A Python virtual environment is created at `/opt/fogbed/venv`. This environment isolates Fogbed's Python libraries from system libraries, avoiding version conflicts. Inside the virtual environment, the script installs the `fogbed` and `containernet` libraries using `pip`.

### 5. System Commands Configuration

To facilitate the use of the Fogbed, the script performs the following actions:

- Creates a wrapper script at `/usr/local/bin/fogbed` that allows executing Python scripts with Fogbed's virtual environment from any directory.
- Creates a symbolic link to Mininet's `mn` executable at `/usr/local/bin/mn`, making it globally accessible. This can be particularly useful after a Fogbed experiment finishes with an error, allowing you to run the sudo mn -c (clean) command from any system path.

### 6. Systemd Service Configuration

By default, the script configures a systemd service called `fogbed-worker.service`. This service turns your machine into a "worker node" that can be remotely controlled by a Fogbed distributed emulation experiment. It ensures that the Fogbed worker process runs as root in the background and is automatically restarted in case of failures. This service is not necessary if you only intend to run local experiments or if your machine is used only to control a distributed experiment (rather than acting as a worker node). The creation of this service can be disabled with the -systemd-disabled flag.

## Script Options

The installation script accepts the following parameters:

| Parameter | Description |
|---|---|
| (none) | Executes the complete installation process. |
| `-remove` | Removes the Fogbed installation, including the working directory and the `systemd` service. |
| `-systemd-disabled` | Installs Fogbed but skips the `systemd` service configuration step. |
| `-h`, `--help` | Displays a help message with available options. |

## Get Started
After having installed fogbed you can start an example topology, copy the example in `examples/sensors/sensors.py` and run with:
```
fogbed run sensors.py
```
Then access the url `http://localhost:3000` on your browser to visualize a React application consuming a REST API what monitor some devices which send health random data.

![monitor](https://user-images.githubusercontent.com/33939999/202031666-45889ae0-49ee-4a5e-a7a6-94f1705a8a08.jpeg)

## Documentation
Project documentation is available at https://larsid.github.io/fogbed/

## Publications
A. Coutinho, U. Damasceno, E. Mascarenhas, A. C. Santos, J. E. B. T. da Silva and F. Greve, "[Rapid-Prototyping of Integrated Edge/Fog and DLT/Blockchain Systems with Fogbed](https://ieeexplore.ieee.org/document/10279234)," ICC 2023 - IEEE International Conference on Communications, Rome, Italy, 2023, pp. 622-627, doi: 10.1109/ICC45041.2023.10279234.
