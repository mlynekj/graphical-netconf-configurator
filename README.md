# GNC - Graphical NETCONF Configurator

## Installation and launching

This application was tested for python 3.13.2. Other versions may work, but are not guaranteed to.

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
