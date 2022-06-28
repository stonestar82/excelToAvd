import xlrd
from operator import *
from generators.envirmentVariables import *
from domain.GeneralInfo import *

def parseGeneralInfo(inventory_file):
	# configuration_variable_mappers = {"CVP IP Addresses": "cvp_instance_ips", "CVP Ingest Auth Key": "cvp_ingestauth_key",
	# "Management Gateway":"mgmt_gateway",  "DNS Servers":"name_servers", "NTP Servers": "ntp_servers",
	# "cvpadmin password sha512 hash":"cvpadmin_pass", "admin password sha512 hash":"admin_pass"}

	gc = GenernalConfiguration()

	configuration_variable_mappers = {
		gc.managementInterface:"mgmt_interface", 
		gc.managementInterfaceVrf:"mgmt_interface_vrf", 
		gc.managementGateway:"mgmt_gateway",
		gc.dnsServers:"name_servers", 
		gc.ntpServers: "ntp_servers",
		gc.adminPassword:"admin_info",
		gc.ansiblePassword:"ansible_info"
	}

	workbook = xlrd.open_workbook(inventory_file)
	info_worksheet = workbook.sheet_by_name(gc.sheetName)
	info = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, info_worksheet.nrows):
			k, v = info_worksheet.cell_value(row,0), info_worksheet.cell_value(row,1)
			if k in configuration_variable_mappers.keys():
					info[configuration_variable_mappers[k]] = v

	general_info = {}

	##### ansible/admin 계정 세팅 S
	# ansible 계정은 기본 설정
	general_info["local_users"] = {
			"ansible":{
					"privilege": 15,
					"role": "network-admin",
					"sha512_password": info["ansible_info"]
			}
	}

	# admin 계정은 값을 등록했을경우만 변경
	if ne(info["admin_info"], ""):
		general_info["local_users"].setdefault(
			"admin" , {
					"privilege": 15, "role": "network-admin", "sha512_password": info["admin_info"]
				}
		)
  	
	###### ansible/admin 계정 세팅 E
	
	###### management interface 세팅 S
	info["mgmt_interface"] = info.get("mgmt_interface", MGMT_INTERFACE)	
	info["mgmt_interface_vrf"] = info.get("mgmt_interface_vrf", MGMT_INTERFACE_VRF)

	general_info["mgmt_interface"] = info["mgmt_interface"]
	general_info["mgmt_interface_vrf"] = info["mgmt_interface_vrf"]
	general_info["mgmt_gateway"] = info["mgmt_gateway"]
	###### management interface 세팅 E 

	# general_info["cvp_instance_ips"] = [ip.strip() for ip in info["cvp_instance_ips"].split(",") if ip != ""]

	# general_info["cvp_ingestauth_key"] = info["cvp_ingestauth_key"] if info["cvp_ingestauth_key"] != "" else None
	
	# Name Server, NTP Server 세팅
	general_info["name_servers"] = [ip.strip() for ip in info["name_servers"].split(",") if ip != ""]
	general_info["ntp_servers"] = [ip.strip() for ip in info["ntp_servers"].split(",") if ip != ""]
	return general_info

def generateGroupVarsAll(inventory_file):
    return parseGeneralInfo(inventory_file)