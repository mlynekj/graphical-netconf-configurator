# GNC - Graphical NETCONF Configurator

This tool is a graphical network configuration tool built with graphical visualization in mind. This tool is meant to be used with Cisco or Juniper Devices, but further extension is possible and encouraged.

Currently the tool supports:

- Configuring **IP addresses** on various interfaces
- Configuraing **hostname** of the device
- Batch configuration of **OSPF** routing protocol
- **IPsec tunnel** configuration, with PSK authentication method
- **VLAN** configuration on switched interfaces, with the ability to switch the interface to L3 mode, for Inter-VLAN on an L3 switch

## Example usage

### IP addresses

### OSPF

### IPsec

### VLAN


## Installation and launching

This application was tested for Python 3.13.2. Other versions may work, but are not guaranteed to.

### Manually

Clone this repository:

```bash
git clone https://github.com/yakubcze/graphical-netconf-configurator.git
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

- On Windows:

```bash
    venv\Scripts\activate
```

- On Linux:

```bash
    source venv/bin/activate
```

Install the required packages:

```bash
(venv) pip install -r requirements.txt
```

Launch the application:

```bash
(venv) python main.py
```

### PyInstaller

To create a standalone executable, you can use PyInstaller. First, install PyInstaller if you haven't already. Install it in the virtual environment you created for this project:

```bash
(venv) pip install pyinstaller
```

Then, run the following command in the terminal:

```bash
(venv) pyinstaller main.spec
```

Then you can find the executable in the `dist` folder. You can run it directly without needing to install Python or any dependencies.
