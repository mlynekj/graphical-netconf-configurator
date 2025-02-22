# YANG Models

This folder contains all YANG models (their snippets) used in the code. Models are in the XML format. The models are divided into the following categories:

- `interfaces/` - models used for interface configuration and monitoring
- `routing/` - models used for routing configuration and monitoring
- `system/` - models used for system configuration and monitoring (e.g. hostname)

The files in all subfolders follow the same naming convention:
``model-name_operation_description.xml``

where:

- `model-name` is the name of the YANG model.
- `operation` is the operation that the file is used in.
  - get
  - get-config
  - edit-config
  - dispatch (used for sending RPCs)
- `description` is a short description of what the file is used for.

For example, the file `openconfig-interfaces_editconfig_edit_ipaddress.xml` is an XML snippet of the `openconfig-interfaces` model used for editing an IP address on an interface.

The models used in the code are of many different types, including vendor native and standard (Cisco-IOS-XE-Native, Openconfig, IETF).