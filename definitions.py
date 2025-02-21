import os, sys

# PATHS
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
XML_DIR = os.path.join(ROOT_DIR, "xml/")
CISCO_XML_DIR = os.path.join(XML_DIR, "cisco/")
OPENCONFIG_XML_DIR = os.path.join(XML_DIR, "openconfig/")
JUNIPER_XML_DIR = os.path.join(XML_DIR, "juniper/")

# CONSTANTS
# Defines the target datastore for configuration changes
CONFIGURATION_TARGET_DATASTORE = "candidate"

# OUTPUT REDIRECTION
# Defines whether to redirect stdout and stderr to the integrated console
STDOUT_TO_CONSOLE = True
STDERR_TO_CONSOLE = False

# DARK MODE
DARK_MODE = False
# TODO: check on linux