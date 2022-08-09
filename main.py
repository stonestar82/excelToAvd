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

def taskPrint(task):
	task = task + " "
	print(task.ljust(100, "*") + "\n")

def main():
    
	taskPrint("TASK [Start]")
	parser = argparse.ArgumentParser(
			description='Creates necessary files to run Arista AVD ansible playbook')
	parser.add_argument('-f', '--file', help="path to Excel file")

	#########################
	##### cvp 기능 제외 #####
	#########################
	# cvpadmin_password = getpass("cvpadmin password: ")
	# confirm_password = getpass("Confirm cvpadmin password: ")
	# if cvpadmin_password != confirm_password:
	#     print("Passwords do not match")
	#     return

	file_location = "./upload/inventory.xlsx"
	if file_location is None:
			print("Please specify a path for the Excel file by using -f. Enter 'python main.py -h' for more details.")
			return
	fabric_name = getFabricName(file_location)
	avd = {
		"inventory": None,
		"group_vars": {
			fabric_name: None,
			fabric_name + "_FABRIC": None,
			fabric_name + "_TENANTS_NETWORKS": None,
			fabric_name + "_SERVERS": None
			},
		"requirements": None,
	}
	avd["requirements"] = '''ansible==2.9.2
		netaddr==0.7.19
		Jinja2==2.10.3
		requests==2.22.0
		treelib==1.5.5
		pytest==5.3.4
		pytest-html
		ward==0.34.0b0
		git+https://github.com/batfish/pybatfish.git
		cvprac==1.0.4'''

	taskPrint("TASK [inventory Parsing]")
	avd["inventory"] = generateInventory(file_location)
	# avd["dc-fabric-deploy-cvp"] = generateCVPDeploymentPlaybook(file_location)

	# ALL -> fabric_name 으로 변경
	avd["group_vars"][fabric_name] = generateGroupVarsAll(file_location) 
	# avd["group_vars"]["CVP"] = generateGroupVarsCVP(file_location, cvpadmin_password)

	taskPrint("TASK [Group Vars Fabric Parsing]")
	avd["group_vars"][fabric_name + "_FABRIC"] = generateGroupVarsFabric(file_location)
	# avd["group_vars"]["SPINES"] = generateGroupVarsSpines(file_location)
	# avd["group_vars"]["L3_LEAFS"] = generateGroupVarsL3Leafs(file_location)
	# avd["group_vars"]["L2_LEAFS"] = generateGroupVarsL2Leafs(file_location)

	taskPrint("TASK [Group Vars Tenants Parsing]")
	avd["group_vars"][fabric_name + "_TENANTS_NETWORKS"] = generateGroupVarsTenants(file_location)

	taskPrint("TASK [Group Vars Servers Parsing]")
	avd["group_vars"][fabric_name + "_SERVERS"] = generateGroupVarsServers(file_location)

	#Create avd directory
	if not os.path.exists("./.ansible"):
			os.mkdir("./.ansible")
			os.mkdir("./.ansible/collections")

	#Create intended directories
	# if not os.path.exists("./inventory/intended/batfish"):
	#     os.makedirs("./inventory/intended/batfish")
	if not os.path.exists("./inventory/intended/configs"):
			os.makedirs("./inventory/intended/configs")
	if not os.path.exists("./inventory/intended/structured_configs"):
			os.makedirs("./inventory/intended/structured_configs")
	# if not os.path.exists("./inventory/intended/structured_configs/cvp"):
	#     os.makedirs("./inventory/intended/structured_configs/cvp")

	#Create documentation directory
	if not os.path.exists("./inventory/documentation/{}".format(fabric_name)):
			os.makedirs("./inventory/documentation/{}".format(fabric_name))
	if not os.path.exists("./inventory/documentation/devices"):
			os.makedirs("./inventory/documentation/devices")		

	#Create inventory file
	# yaml.dump시 sort_keys=False 값을 주지 않으면 키값 기준으로 오름차순으로 정렬되어 적용됨
	# sort_keys=False 실제 적용한 값 순서대로 처리
	taskPrint("TASK [inventory.yml Generate]")
	with BlankNone(), open("./inventory/inventory.yml", "w") as inv:
			inv.write(yaml.dump(avd["inventory"], sort_keys=False))

	taskPrint("TASK [Group Vars *.yml Generate]")
	#Create group_vars files
	if not os.path.exists("./inventory/group_vars"):
			os.mkdir("./inventory/group_vars")
	for k, v in avd["group_vars"].items():
			path = "./inventory/group_vars/{}.yml".format(k)
			with open(path, "w") as gvfile:
					gvfile.write(yaml.dump(v))

	##### ansible.cfg 고정으로 변경
	# ansible.cfg 파일 생성
	# taskPrint("TASK [ansible.cfg Generate]")
	# with open("./ansible.cfg", "w") as ans_cfg:
	# 		ans_cfg.write(ANSIBLE_CONFIG)
	
	#Create dc-fabric-deploy-cvp.yml
	# with open("./inventory/dc-fabric-deploy-cvp.yml", "w") as ans_pb:
	#     ans_pb.write(avd["dc-fabric-deploy-cvp"])

	#Create requirements file
	# with open("./inventory/requirements.txt", "w") as reqs:
	# 		reqs.write(avd["requirements"])

	# deploy playbook 생성
	taskPrint("TASK [deploy.yml PlayBook Generate]")
	data = { "fabricName" : fabric_name }
	with open('./templates/deploy.j2') as f:
		template = Template(f.read())

	with open("./deploy.yml", "w") as reqs:
			reqs.write(template.render(**data))

	# taskPrint("TASK [deploy.yml PlayBook Exec]")
	# os.system("ansible-playbook deploy.yml")

    #Install requirements
    # process = subprocess.Popen(['pip', 'install', '-r', './avd/requirements.txt'],
    #                  stdout=subprocess.PIPE, 
    #                  stderr=subprocess.PIPE)
    # stdout, stderr = process.communicate()

    #Create dc-fabric-post-validation.yml

if __name__ == "__main__":
	main()