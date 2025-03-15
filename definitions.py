import os, sys

# PATHS
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
YANG_DIR = os.path.join(ROOT_DIR, "yang/")
INTERFACES_YANG_DIR = os.path.join(YANG_DIR, "interfaces/")
ROUTING_YANG_DIR = os.path.join(YANG_DIR, "routing/")
SYSTEM_YANG_DIR = os.path.join(YANG_DIR, "system/")
SECURITY_YANG_DIR = os.path.join(YANG_DIR, "security/")
VLAN_YANG_DIR = os.path.join(YANG_DIR, "vlan/")

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