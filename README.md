# GNC - Graphical NETCONF Configurator

This tool, called GNC, is a graphical network configuration tool built with graphical visualization in mind. It was built as a part of my diploma thesis at VŠB-TUO called "*Advanced Tools for automatic configuration of network devices using NETCONF*".
It allows to configure network devices using the NETCONF protocol, while allowing to visaulize the topology in a graphical way. Topology visualization is done by connecting the devices on the canvas using cables on the specified interfaces. If the interface has an IP address assigned, it will be shown as well.

![cable](https://github.com/user-attachments/assets/e94b7d48-af66-4771-bae5-6a5dd52fb6ee)

GNC is, in its current state, meant to be used with Cisco or Juniper Devices, but further extension is possible and encouraged.

GNC was built in Python, primarily using these modules:
- *ncclient* for NETCONF communication
- *Qt* for GUI
- *ipaddress* for convenient way of handling IP addresses
- *lxml* for parsing and building XML payload

Currently the tool supports the following functions:

- Configuring **IP addresses** on various interfaces
- Configuraing **hostname** of the device
- Batch configuration of **OSPF** routing protocol
- **IPsec tunnel** configuration, with PSK authentication method
- **VLAN** configuration on switched interfaces, with the ability to switch the interface to L3 mode, for Inter-VLAN on an L3 switch

## Cadidate datastore

This application communicates with the network device using the NETCONF protocol, using various YANG models. GNC uses the candidate datastore feature. To administer this datastore, the application allows:

- Storing each RPC message sent, including its corresponding response, with the ability of showing the information.
![candidate](https://github.com/user-attachments/assets/7804bccb-efe8-4eb4-8c20-c601f924b23a)

- Confirming the commit, using the "Confirmed commit" NETCONF standard operation defined in the RFC6241. The confirmed commit sets a timeout, with the ability to rollback the changes during the timeout.
![confirmed](https://github.com/user-attachments/assets/a22aa047-122c-4248-aec6-42c388940b30)



## Example usage

### IP addresses

https://github.com/user-attachments/assets/31fc0f2d-5c39-4015-8d44-9b45f7cc9c94

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
