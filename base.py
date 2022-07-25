import yaml, os, subprocess
from generators.generateInventory import generateInventory, getFabricName
from generators.generateGroupVarsAll import generateGroupVarsAll
from generators.generateGroupVarsFabric import generateGroupVarsFabric
from generators.generateGroupVarsTenants import generateGroupVarsTenants
from generators.generateGroupVarsServers import generateGroupVarsServers
from generators.envirmentVariables import *
from jinja2 import Template
from generators.BlankNone import BlankNone

import argparse
from getpass import getpass


def taskPrint(task):
	task = task + " "
	print(task.ljust(100, "*") + "\n")

def main():
    
	taskPrint("TASK [Start]")
	parser = argparse.ArgumentParser(
			description='Creates necessary files to run Arista AVD ansible playbook')
	parser.add_argument('-f', '--file', help="path to Excel file")
	args = parser.parse_args()

	#########################
	##### cvp 기능 제외 #####
	#########################
	# cvpadmin_password = getpass("cvpadmin password: ")
	# confirm_password = getpass("Confirm cvpadmin password: ")
	# if cvpadmin_password != confirm_password:
	#     print("Passwords do not match")
	#     return

	file_location = "/workspace/excelToAvd/inventory.xlsx"
	if file_location is None:
			print("Please specify a path for the Excel file by using -f. Enter 'python main.py -h' for more details.")
			return
	
	hosts = generateGroupVarsFabric(file_location)

	taskPrint("TASK [config file *.cfg Generate]")
	
	with open('/workspace/excelToAvd/templates/base.j2') as f:
		template = Template(f.read())

	for host in hosts["node"].items():
			path = "/workspace/excelToAvd/inventory/intended/configs/{}.cfg".format(k)
			
	
	# deploy playbook 생성
	taskPrint("TASK [deploy.yml PlayBook Generate]")
	
	with open('/workspace/excelToAvd/templates/deploy.j2') as f:
		template = Template(f.read())

	with open("/workspace/excelToAvd/deploy.yml", "w") as reqs:
			reqs.write(template.render(**data))

	taskPrint("TASK [deploy.yml PlayBook Exec]")
	os.system("ansible-playbook deploy.yml")



if __name__ == "__main__":
	main()