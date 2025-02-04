# Interfaces Dictionary

NOTE: outdated

Instance of a Device stores all interface parameters in a dictionary called interfaces. The dictionary is structured as follows:

```python
{
    "interface_name": {
        "admin_status": "UP" or "DOWN",
        "oper_status": "UP" or "DOWN",
        "subinterfaces": {
            "subinterface_name": {
                "ipv4_data": [IPv4Interface("ip_address/prefix_length")],
                "ipv6_data": [IPv6Interface("ip_address/prefix_length")],
            }
        }
    }
}
```

Example (Retrieved from Juniper vRouter:)

```python
Device.interfaces = {
    "lsi": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "dsc": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "lo0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {
            "16384": {"ipv4_data": [IPv4Interface("127.0.0.1/32")], "ipv6_data": []},
            "16385": {"ipv4_data": [], "ipv6_data": []},
        },
    },
    "gre": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "ipip": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "tap": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "pime": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "pimd": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fxp0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {
            "0": {"ipv4_data": [IPv4Interface("172.16.10.83/24")], "ipv6_data": []}
        },
    },
    "em1": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {
            "0": {
                "ipv4_data": [
                    IPv4Interface("10.0.0.4/8"),
                    IPv4Interface("128.0.0.1/2"),
                    IPv4Interface("128.0.0.4/2"),
                ],
                "ipv6_data": [
                    IPv6Interface("fe80::5254:ff:fe12:bdfe/64"),
                    IPv6Interface("fec0::a:0:0:4/64"),
                ],
            }
        },
    },
    "mtun": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "jsrv": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {
            "1": {"ipv4_data": [IPv4Interface("128.0.0.127/2")], "ipv6_data": []}
        },
    },
    "demux0": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "cbp0": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "pip0": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "pp0": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "irb": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "vtep": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "esi": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "rbeb": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti0": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti1": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti2": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti3": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti4": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti5": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti6": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "fti7": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "mif": {"admin_status": "UP", "oper_status": "UP", "subinterfaces": {}},
    "lc-0/0/0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"32769": {"ipv4_data": [], "ipv6_data": []}},
    },
    "pfh-0/0/0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {
            "16383": {"ipv4_data": [], "ipv6_data": []},
            "16384": {"ipv4_data": [], "ipv6_data": []},
        },
    },
    "pfe-0/0/0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16383": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/0": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/1": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/2": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/3": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/4": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/5": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/6": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/7": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/8": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
    "ge-0/0/9": {
        "admin_status": "UP",
        "oper_status": "UP",
        "subinterfaces": {"16386": {"ipv4_data": [], "ipv6_data": []}},
    },
}
```