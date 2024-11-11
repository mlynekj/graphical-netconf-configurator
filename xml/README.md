File structure:
For each YANG model, there is a directory with the name of the YANG model. Inside each YANG model directory, there are subdirectories containing XML's separated by the python modules that use them (as in the /modules directory).

Each file is named after the ncclient operation that is being performed, and the function that is being manipulated with. Example: get_config-hostname.xml
```
/xml/
├── cisco/
│   └── system/
└── openconfig/
    ├── system/
    └── interfaces/
```