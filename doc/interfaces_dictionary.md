# Interfaces Dictionary

Instance of a Device stores all interface parameters in a dictionary called interfaces. The dictionary is structured as follows:

```python
{
    "interface_name": {
        "admin_status": "UP" or "DOWN",
        "oper_status": "UP" or "DOWN",
        "description": None,
        "flag": "commited",
        "subinterfaces": {
            "subinterface_id": {
                "ipv4_data": [{"value": IPv4Interface("xxx.xxx.xxx.xxx/xx"), "flag": "commited"}],
                "ipv6_data": [{"value": IPv6Interface("xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/xx"), "flag": "commited"}],
            }
        }
    }
}
```

Example (Retrieved from Cisco IOS XE Router:)

```python
device.interfaces = {
    "GigabitEthernet1": {
        "admin_status": "UP",
        "oper_status": "UP",
        "description": None,
        "flag": "commited",
        "subinterfaces": {
            "0": {
                "ipv4_data": [
                    {"value": IPv4Interface("100.1.0.1/24"), "flag": "commited"}
                ],
                "ipv6_data": [],
            }
        },
    },
    "GigabitEthernet2": {
        "admin_status": "UP",
        "oper_status": "UP",
        "description": None,
        "flag": "commited",
        "subinterfaces": {
            "0": {
                "ipv4_data": [
                    {"value": IPv4Interface("100.0.0.2/24"), "flag": "commited"}
                ],
                "ipv6_data": [],
            }
        },
    },
    "GigabitEthernet3": {
        "admin_status": "UP",
        "oper_status": "UP",
        "description": None,
        "flag": "commited",
        "subinterfaces": {"0": {"ipv4_data": [], "ipv6_data": []}},
    },
    "GigabitEthernet4": {
        "admin_status": "UP",
        "oper_status": "UP",
        "description": None,
        "flag": "commited",
        "subinterfaces": {
            "0": {
                "ipv4_data": [
                    {"value": IPv4Interface("172.16.10.82/24"), "flag": "commited"}
                ],
                "ipv6_data": [],
            }
        },
    },
}
```
