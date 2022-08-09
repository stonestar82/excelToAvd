import requests, subprocess, json
from operator import ne, eq
from EapiClientLib import EapiClient
from string import Template


class ZtpError(Exception):
  pass

def taskPrint(task):
  task = task + " "
  print(task.ljust(100, "*") + "\n")
		

def main():
	taskPrint("TASK [Start]")	
	taskPrint("TASK [spine, leaf count confirm]")

	t = """
!
logging console informational
logging monitor informational
logging synchronous level all
!
username ${ansible} secret ${ansible_pw} privilege 15
!
ip routing
vrf instance MGMT
!
interface Management1
   description oob_management
   no shutdown
   vrf MGMT
   ip address ${ip}/24
!
ip route vrf MGMT 0.0.0.0/0 ${gateway}.1
	"""
	
	switch = EapiClient(disableAaa=True, privLevel=15)

	taskPrint("TASK [LLDP]")

	cli_command = "show ip interface brief | json"
	result = switch.runCmds( 1, [cli_command])
	data = result["result"]


	ip = data[0]["interfaces"]["Management1"]["interfaceAddress"]["ipAddr"]["address"]
	tmp_ip = ip.split(".")	
	gateway = tmp_ip[0] + "." + tmp_ip[1] + "." + tmp_ip[2]

	data = { "ansible" : "ansible", "ansible_pw": "ansible", "ip" : ip, "gateway": gateway }
	
	template = Template(t)

	with open("gen-config", "w") as reqs:
			reqs.write(template.substitute(data))	
	
	taskPrint("TASK [cfg startup-config copy]")

	cli_command = "mv gen-config /mnt/flash/startup-config"
	subprocess.call(cli_command, shell=True)

	taskPrint("TASK [complete]")

	cli_command = "reboot"
	subprocess.call(cli_command, shell=True)

if __name__ == '__main__':
    main()