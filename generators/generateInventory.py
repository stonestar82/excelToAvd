from pickle import NONE
import xlrd, re
import yaml

def convertToBoolIfNeeded(variable):
	if type(variable) == str and re.match(r'(?i)(True|False)', variable.strip()):
		variable = True if re.match(r'(?i)true', variable.strip()) else False
	return variable

def getFabricName(inventory_file):
	workbook = xlrd.open_workbook(inventory_file)
	info_worksheet = workbook.sheet_by_name("General Configuration Details")
	# transform the workbook to a list of dictionaries
	for row in range(1, info_worksheet.nrows):
		k, v = info_worksheet.cell_value(row,0), info_worksheet.cell_value(row,1)
		if k == "Fabric Name":
			v = v if v != "" else None
			return v
	return None

def getCVPAddresses(inventory_file):
	workbook = xlrd.open_workbook(inventory_file)
	info_worksheet = workbook.sheet_by_name("General Configuration Details")
	# transform the workbook to a list of dictionaries
	for row in range(1, info_worksheet.nrows):
		k, v = info_worksheet.cell_value(row,0), info_worksheet.cell_value(row,1)
		if k == "CVP IP Addresses":
			return [ip.strip() for ip in v.split(",") if ip != ""]
	return None

def getCVPInventory(inventory_file):
	cvp_addresses = getCVPAddresses(inventory_file)
	cvp_dict = {"hosts": {}}
	cvp_node_names = ["cvp_primary", "cvp_secondary", "cvp_tertiary"]
	for i, address in enumerate(cvp_addresses):
		cvp_dict["hosts"][cvp_node_names[i]] = {
			"ansible_httpapi_host": address,
			"ansible_host": address
		}
		break
	return cvp_dict

def parseSuperSpineInfo(inventory_file):
	'''
	'''
	spines_info = {"vars": {"type": "super-spine"}, "hosts": {}}
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name("Spine Info")
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		spine_info = {}
		for col in range(inventory_worksheet.ncols):
			spine_info[first_row[col]]=inventory_worksheet.cell_value(row,col)
		
		if convertToBoolIfNeeded(spine_info["Super Spine"]):
			hostname = spine_info["Hostname"]
			spines_info["hosts"][hostname] = {"ansible_host": spine_info["Management IP"].split("/")[0]}
	return spines_info

def parseSpineInfo(inventory_file):
	'''
	'''
	spines_info = {"vars": {"type": "spine"}, "hosts": {}}
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name("Spine Info")
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		spine_info = {}
		for col in range(inventory_worksheet.ncols):
			spine_info[first_row[col]]=inventory_worksheet.cell_value(row,col)
		
		# if not convertToBoolIfNeeded(spine_info["Super Spine"]):
		hostname = spine_info["Hostname"]
		spines_info["hosts"][hostname] = {"ansible_host": spine_info["Management IP"].split("/")[0]}
	return spines_info

def parseLeafInfo(inventory_file, leaf_type="L3"):
	'''
	type: options are 'L3' or 'L2'
	'''
	leafs = {}
	workbook = xlrd.open_workbook(inventory_file)
	sheetname = "L3 Leaf Info" if leaf_type == "L3" else "L2 Leaf Info"
	leafTypeName = "l3leaf" if leaf_type == "L3" else "l2leaf"
	inventory_worksheet = workbook.sheet_by_name(sheetname)
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		leaf_info = {}
		for col in range(inventory_worksheet.ncols):
			leaf_info[first_row[col]]=inventory_worksheet.cell_value(row,col)
		hostname = leaf_info["Hostname"]
		node_details = {}
		node_details["ansible_host"] = leaf_info["Management IP"].split("/")[0]
		if leaf_info["Container Name"] not in node_groups.keys():
			node_groups[leaf_info["Container Name"]] = {
				"vars": {"type": leafTypeName},
				"hosts": {hostname: node_details}
			}
		else:
			node_groups[leaf_info["Container Name"]]["hosts"][hostname] = node_details

	if len(node_groups) > 0: 
		leafs["children"] = node_groups
		return leafs
	else:
		return None

def getServers(fabric_name):
	servers = {"children": {fabric_name + "_L3LEAFS": None, fabric_name + "_L2_LEAFS": None}}
	return servers

def getTenantNetworks(fabric_name):
	tn = {"children": {fabric_name + "_L3LEAFS": None, fabric_name + "_L2LEAFS": None}}
	return tn

def getFabricInventory(inventory_file, fabric_name):
	fabric_inventory = {"children":{}}

	# fabric_inventory["children"][fabric_name+"_SUPERSPINES"] = parseSuperSpineInfo(inventory_file)

	fabric_inventory["children"][fabric_name+"_SPINES"] = parseSpineInfo(inventory_file)
	
	if parseLeafInfo(inventory_file, leaf_type="L3") != None:
		fabric_inventory["children"][fabric_name+"_L3LEAFS"] = parseLeafInfo(inventory_file, leaf_type="L3")

	if parseLeafInfo(inventory_file, leaf_type="L2") != None:
		fabric_inventory["children"][fabric_name+"_L2LEAFS"] = parseLeafInfo(inventory_file, leaf_type="L2")
		
	fabric_inventory["vars"] = {
		"ansible_connection": "network_cli",
		"ansible_network_os": "eos",
		"ansible_become": True,
		"ansible_user": "ansible",
    "ansible_ssh_pass": "ansible",
		"ansible_become_method": "enable",
		"ansible_httpapi_use_ssl": False,
		"ansible_httpapi_validate_certs": False
	}
	return fabric_inventory

def generateInventory(inventory_file):
	fabric_name = getFabricName(inventory_file)
	if fabric_name is None:
		return

	inventory = {
		"all": {
			"children": {
				fabric_name: {
					"children": {
						fabric_name + "_FABRIC": {
							"children": { 
								fabric_name + "_SUPERSPINES" : None,
								fabric_name + "_SPINES" : None,
								fabric_name + "_L3LEAFS" : None,
								fabric_name + "_L2LEAFS" : None								
							}
						}
					}					
				}
			}
		}
	}
	# #Add CVP info
	# inventory["all"]["children"]["CVP"] = getCVPInventory(inventory_file)

	#Add Fabric info
	inventory["all"]["children"][fabric_name]["children"][fabric_name + "_FABRIC"] = getFabricInventory(inventory_file, fabric_name)

	# inventory = {"all":{"children":{
	#     "CVP": None,
	#     fabric_name: None
	# }}}
	#Add CVP info
	# inventory["all"]["children"]["CVP"] = getCVPInventory(inventory_file)

	# #Add Fabric info
	# inventory["all"]["children"][fabric_name] = getFabricInventory(inventory_file)

	#Add Servers
	inventory["all"]["children"][fabric_name+"_SERVERS"] = getServers(fabric_name)

	#Add Tenant Networks
	inventory["all"]["children"][fabric_name+"_TENANTS_NETWORKS"] = getTenantNetworks(fabric_name)

	return inventory

if __name__ == "__main__":
    generateInventory("PotentialAnsibleCSVTemplate.xlsx")