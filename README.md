![](https://img.shields.io/badge/python-3.8+-blue.svg)
![](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)
# Fogbed

Fogbed is a framework and toolset integration for rapid prototyping of fog components in virtualized environments using a desktop or distributed approach. Its design meets the postulated requirements of low cost, flexible setup and compatibility with real world technologies. The components are based on Mininet network emulator with Docker container instances as fog virtual nodes.

## Install

All installation and dependency management steps are automated in the `install-fogbed.sh` script. The script installs Containernet/Mininet, Fogbed and their required packages in the /opt/fogbed/venv directory. Also the script can also uninstall an existing setup when needed. During installation it checks for required system packages, configures Docker and Python dependencies, sets up the Fogbed Python package in editable mode, and optionally registers the Fogbed systemd service so the controller can be started at boot.

```bash
wget https://raw.githubusercontent.com/larsid/fogbed/main/install-fogbed.sh
chmod +x install-fogbed.sh
sudo ./install-fogbed.sh
```

Run `sudo ./install-fogbed.sh --help` to see the available options, including reinstalling without the systemd service or removing an existing installation.

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
