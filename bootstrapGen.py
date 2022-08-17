# -*- coding: utf-8 -*-
#!/usr/bin/env python
from datetime import datetime
from string import Template
import json

def bootstrapFirstBootPythonCreate():
		
	with open("switchInit.json", "r") as f:
		config = json.load(f)

	url = config["url"]
		
	t = """#!/usr/bin/env python
import requests
from EapiClientLib import EapiClient
from string import Template
from datetime import datetime

t = \"\"\"
!
logging buffered 1000
logging console informational
logging monitor informational
logging synchronous level all
!
username $${ansible} secret $${ansible_pw} privilege 15
!
ip routing
!
interface Management1
	description oob_management
	no shutdown
	ip address $${ip}/24
!
ip route 0.0.0.0/0 $${gateway}.1
\"\"\"

switch = EapiClient(disableAaa=True, privLevel=15)

cli_command = "sh version | json"
result = switch.runCmds( 1, [cli_command])
data = result["result"][0]
sysmac = data["systemMacAddress"]
serial = data["serialNumber"]

requestUrl = "${requestUrl}/bootstrap/requestip/${seq}/" + sysmac + "/" + serial

response = requests.get(requestUrl)
ip = response.text

tmp_ip = ip.split(".")	
gateway = tmp_ip[0] + "." + tmp_ip[1] + "." + tmp_ip[2]

data = { "ansible" : "ansible", "ansible_pw": "ansible", "ip" : ip, "gateway": gateway }

template = Template(t)

with open("/mnt/flash/startup-config", "w") as reqs:
	reqs.write(template.substitute(data))


	"""
	now = datetime.now()

	now = now.strftime("%Y%m%d%H%M")

	template = Template(t)

	data = { "seq" : now, "requestUrl": url }

	with open("bootstrap", "w") as reqs:
		reqs.write(template.substitute(data))
