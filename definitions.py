import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
XML_DIR = os.path.join(ROOT_DIR, "xml/")

CISCO_XML_DIR = os.path.join(XML_DIR, "cisco/")
OPENCONFIG_XML_DIR = os.path.join(XML_DIR, "openconfig/")

CONFIGURATION_TARGET = "candidate"