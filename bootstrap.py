#!/usr/bin/env python
from EapiClientLib import EapiClient
from string import Template

t = "username ${ansible} secret ${ansible_pw} privilege 15"
data = { "ansible" : "ansible", "ansible_pw": "ansible" }

template = Template(t)
cmd = template.substitute(data)

cmds = ["logging buffered 1000", "logging console informational", "logging monitor informational", "logging synchronous level all", cmd]	

switch = EapiClient(disableAaa=True, privLevel=15)

switch.runCmds( 1, ["enable"] + cmds)