# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the eos_ospf_interfaces module
"""


class Ospf_interfacesArgs(object):  # pylint: disable=R0903
    """The arg spec for the eos_ospf_interfaces module"""

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "state": {
            "default": "merged",
            "type": "str",
            "choices": [
                "merged",
                "replaced",
                "overridden",
                "deleted",
                "gathered",
                "parsed",
                "rendered",
            ],
        },
        "running_config": {"type": "str"},
        "config": {
            "elements": "dict",
            "type": "list",
            "options": {
                "name": {"type": "str"},
                "address_family": {
                    "elements": "dict",
                    "type": "list",
                    "options": {
                        "ip_params": {
                            "elements": "dict",
                            "type": "list",
                            "options": {
                                "retransmit_interval": {"type": "int"},
                                "cost": {"type": "int"},
                                "afi": {
                                    "required": True,
                                    "type": "str",
                                    "choices": ["ipv4", "ipv6"],
                                },
                                "area": {
                                    "type": "dict",
                                    "options": {
                                        "area_id": {
                                            "required": True,
                                            "type": "str",
                                        }
                                    },
                                },
                                "bfd": {"type": "bool"},
                                "mtu_ignore": {"type": "bool"},
                                "priority": {"type": "int"},
                                "dead_interval": {"type": "int"},
                                "hello_interval": {"type": "int"},
                                "passive_interface": {"type": "bool"},
                                "transmit_delay": {"type": "int"},
                                "network": {"type": "str"},
                            },
                        },
                        "encryption_v3": {
                            "type": "dict",
                            "options": {
                                "key": {"type": "str", "no_log": True},
                                "algorithm": {
                                    "type": "str",
                                    "choices": ["md5", "sha1"],
                                },
                                "encryption": {
                                    "type": "str",
                                    "choices": [
                                        "3des-cbc",
                                        "aes-128-cbc",
                                        "aes-192-cbc",
                                        "aes-256-cbc",
                                        "null",
                                    ],
                                },
                                "keytype": {"type": "str", "no_log": False},
                                "spi": {"type": "int"},
                                "passphrase": {"type": "str", "no_log": True},
                            },
                        },
                        "cost": {"type": "int"},
                        "afi": {
                            "required": True,
                            "type": "str",
                            "choices": ["ipv4", "ipv6"],
                        },
                        "authentication_v2": {
                            "type": "dict",
                            "options": {
                                "set": {"type": "bool"},
                                "message_digest": {"type": "bool"},
                            },
                        },
                        "bfd": {"type": "bool"},
                        "authentication_v3": {
                            "type": "dict",
                            "options": {
                                "key": {"type": "str", "no_log": True},
                                "spi": {"type": "int"},
                                "keytype": {"type": "str", "no_log": False},
                                "passphrase": {"type": "str", "no_log": True},
                                "algorithm": {
                                    "type": "str",
                                    "choices": ["md5", "sha1"],
                                },
                            },
                        },
                        "retransmit_interval": {"type": "int"},
                        "message_digest_key": {
                            "no_log": False,
                            "type": "dict",
                            "options": {
                                "key_id": {"type": "int"},
                                "key": {"type": "str", "no_log": True},
                                "encryption": {"type": "str"},
                            },
                        },
                        "mtu_ignore": {"type": "bool"},
                        "priority": {"type": "int"},
                        "area": {
                            "type": "dict",
                            "options": {
                                "area_id": {"required": True, "type": "str"}
                            },
                        },
                        "dead_interval": {"type": "int"},
                        "shutdown": {"type": "bool"},
                        "passive_interface": {"type": "bool"},
                        "authentication_key": {
                            "type": "dict",
                            "no_log": False,
                            "options": {
                                "encryption": {"type": "str"},
                                "key": {"type": "str", "no_log": True},
                            },
                        },
                        "hello_interval": {"type": "int"},
                        "transmit_delay": {"type": "int"},
                        "network": {"type": "str"},
                    },
                },
            },
        },
    }  # pylint: disable=C0301
