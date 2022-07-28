from operator import eq, ne
from pprint import pprint
import xlrd
import json, yaml, re
from collections import OrderedDict
from domain.GenernalConfiguration import *
from domain.Spine import *
from domain.SpineDetail import *
from domain.L3Leaf import *
from domain.L3LeafDetail import *
from domain.L2Leaf import *
from domain.L2LeafDetail import *




def convertToBoolIfNeeded(variable):
	if type(variable) == str and re.match(r'(?i)(True|False)', variable.strip()):
		variable = True if re.match(r'(?i)true', variable.strip()) else False
	return variable

def convertToList(key, value, types):

	if (eq("L3", types)):
		obj = L3Leaf()
	else:
		obj = L2Leaf()
	
	keys_that_are_lists = [obj.mlagInterfaces, obj.uplinkSwitches, obj.uplinkInterfaces, obj.uplinkSwitchInterfaces]

	if key in keys_that_are_lists:
		value = [v.strip() for v in value.split(",") if v != ""]
	return value

def consolidateNodeGroups(node_groups):
	# node_group_level_vars = ["bgp_as", "platform", "filter", "parent_l3leafs", "uplink_interfaces"]
	node_group_level_vars = ["filter", "uplink_switches"]
	groups_names = node_groups.keys()
	new_group_vars = {}
	for group, nodes in node_groups.items():
		new_group_vars[group] = {}
		for node, details in nodes.items():               
			if len(details.keys()) > 1:
				host1_vars = details[list(details.keys())[0]]
				host2_vars = details[list(details.keys())[1]]
				for variable, value in host1_vars.items():
					if variable in host2_vars.keys() and host1_vars[variable] == host2_vars[variable]:                        
							new_group_vars[group][variable] = value
					elif variable in node_group_level_vars:
						new_group_vars[group][variable] = value 
			else:
					for variable, value in details[list(details.keys())[0]].items():
						if variable in node_group_level_vars:
							new_group_vars[group][variable] = value 


	# print(json.dumps(new_group_vars, indent=2))
	for group, variables in new_group_vars.items():
		for variable, value in variables.items():
			node_groups[group][variable] = value
			for variable_dict in node_groups[group]["nodes"].values():
				del(variable_dict[variable])
	return node_groups 

def parseL2LeafInfo(inventory_file):
	l2leaf = L2Leaf()
	l2leafDetail = L2LeafDetail()
	l2_yaml = {}
	configuration_variable_mappers = {
		l2leafDetail.platform: "platform", 
		l2leafDetail.uplinkSwitches:"uplink_switches", 
		l2leafDetail.uplinkInterfaces: "uplink_interfaces",
		l2leafDetail.mlagInterfaces:"mlag_interfaces", 
		l2leafDetail.mlag: "mlag", 
		l2leafDetail.mlagPeerIpv4Pool: "mlag_peer_ipv4_pool", 
		l2leafDetail.mlagPeerL3Ipv4Pool: "mlag_peer_l3_ipv4_pool", 
		l2leafDetail.virtualRouterMacAddress: "virtual_router_mac_address", 
		l2leafDetail.spanningTreeMode:"spanning_tree_mode", 
		l2leafDetail.spanningTreePriority:"spanning_tree_priority"
	}
	l2_leaf_info = {}
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name("L2 Leaf Info")
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		l2_leaf_info = {}
		for col in range(inventory_worksheet.ncols):
			l2_leaf_info[first_row[col]]=inventory_worksheet.cell_value(row,col)
		hostname = l2_leaf_info[l2leaf.hostname]
		node_details = {}
		node_details["id"] = int(l2_leaf_info[l2leaf.id])
		node_details["mgmt_ip"] = l2_leaf_info[l2leaf.managementIp]

		if ne(l2_leaf_info[l2leaf.tenats], "") or ne(l2_leaf_info["Tags"], "") :
			node_details["filter"] = {}
			if ne(l2_leaf_info[l2leaf.tenats], ""):
				node_details["filter"]["tenants"] = [tenant.strip() for tenant in l2_leaf_info[l2leaf.tenats].split(",") if tenant != ""]
			if ne(l2_leaf_info[l2leaf.tags], ""):
				node_details["filter"]["tags"] = [tag.strip() for tag in l2_leaf_info[l2leaf.tags].split(",") if tag != ""]
		
		optional_params = {}
		# optional_params["platform"] = str(l2_leaf_info["Platform"]) if l2_leaf_info["Platform"] != "" else None
		optional_params["uplink_switches"] = [spine.strip() for spine in l2_leaf_info[l2leaf.uplinkSwitches].split(",") if spine] if l2_leaf_info[l2leaf.uplinkSwitches] != "" else None
		# optional_params["uplink_interfaces"] = [uplink_iface.strip() for uplink_iface in l2_leaf_info["Uplink Interfaces"].split(",") if uplink_iface] if l2_leaf_info["Uplink Interfaces"] != "" else None
		optional_params["uplink_switch_interfaces"] = [uplink_iface.strip() for uplink_iface in l2_leaf_info[l2leaf.uplinkSwitchInterfaces].split(",") if uplink_iface] if l2_leaf_info[l2leaf.uplinkSwitchInterfaces] != "" else None
		# optional_params["mlag_interfaces"] = [iface.strip() for iface in l2_leaf_info["MLAG Interfaces"].split(",") if iface] if l2_leaf_info["MLAG Interfaces"] != "" else None
		for k, v in optional_params.items():
			if v is not None:
				v = int(v) if type(v) == float else v
				node_details[k] = v

		if l2_leaf_info[l2leaf.containerName] not in node_groups.keys():
			node_groups[l2_leaf_info[l2leaf.containerName]] = {"nodes": {hostname: node_details}}
		else:
			node_groups[l2_leaf_info[l2leaf.containerName]]["nodes"][hostname] = node_details

	# print(yaml.dump(node_groups))
	#parse default values
	l2_defaults_worksheet = workbook.sheet_by_name(l2leafDetail.sheetName)
	defaults = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, l2_defaults_worksheet.nrows):
		k, v = l2_defaults_worksheet.cell_value(row,0), l2_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys() and v is not None and v != "":
			v = convertToList(k, v, "L2")
			v = convertToBoolIfNeeded(v)
			v = int(v) if type(v) == float else v
			defaults[configuration_variable_mappers[k]] = v

	# print(json.dumps(defaults, indent=2))
	l2_yaml["defaults"] = defaults
	l2_yaml["node_groups"] = consolidateNodeGroups(node_groups)

	return l2_yaml

def parseL3LeafInfo(inventory_file):
	l3leaf = L3Leaf()
	l3leafDetail = L3LeafDetail()
	l3_yaml = {}
	configuration_variable_mappers = {
		l3leafDetail.platform: "platform",			
		l3leafDetail.loopbackIpv4Pool: "loopback_ipv4_pool",
		l3leafDetail.loopbackIpv4Offset: "loopback_ipv4_offset",
		l3leafDetail.vtepLoopbackIpv4Pool: "vtep_loopback_ipv4_pool",
		l3leafDetail.uplinkInterfaces: "uplink_interfaces",
		l3leafDetail.uplinkSwitches: "uplink_switches",		
		l3leafDetail.uplinkIpv4Pool: "uplink_ipv4_pool",
		l3leafDetail.mlagInterfaces:"mlag_interfaces", 
		l3leafDetail.mlagPortChannelId:"mlag_port_channel_id", 
		l3leafDetail.mlagPeerIpv4Pool: "mlag_peer_ipv4_pool",
		l3leafDetail.mlagPeerL3Ipv4Pool: "mlag_peer_l3_ipv4_pool",
		l3leafDetail.virtualRouterMacAddress:"virtual_router_mac_address",
		l3leafDetail.spanningTreeMode:"spanning_tree_mode", 
		l3leafDetail.spanningTreePriority:"spanning_tree_priority",
	}

	l3_leaf_info = {}
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name(l3leaf.sheetName)
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		l3_leaf_info = {}
		for col in range(inventory_worksheet.ncols):
			l3_leaf_info[first_row[col]]=inventory_worksheet.cell_value(row,col)
		hostname = l3_leaf_info["Hostname"]
		node_details = {}
		node_details["id"] = int(l3_leaf_info[l3leaf.id])
		node_details["mgmt_ip"] = l3_leaf_info[l3leaf.managementIp]

		if ne(l3_leaf_info[l3leaf.uplinkSwitchInterfaces], ""):
			node_details["uplink_switch_interfaces"] = [upSwitchInt.strip() for upSwitchInt in l3_leaf_info[l3leaf.uplinkSwitchInterfaces].split(",")]

		# node_details["filter"] = {}
		# node_details["filter"]["tenants"] = [tenant.strip() for tenant in l3_leaf_info["Tenants"].split(",") if tenant != ""]
		# node_details["filter"]["tags"] = [tag.strip() for tag in l3_leaf_info["Tags"].split(",") if tag != ""]
		optional_params = {}
		# optional_params["platform"] = str(l3_leaf_info["Platform"]) if l3_leaf_info["Platform"] != "" else None
		# optional_params["spines"] = [spine.strip() for spine in l3_leaf_info["Spines"].split(",") if spine] if l3_leaf_info["Spines"] != "" else None
		# optional_params["uplink_switches"] = [uplink_iface.strip() for uplink_iface in l3_leaf_info["Uplink Switches"].split(",") if uplink_iface] if l3_leaf_info["Uplink Switches"] != "" else None
		# optional_params["uplink_interfaces"] = [uplink_iface.strip() for uplink_iface in l3_leaf_info["Uplink Interfaces"].split(",") if uplink_iface] if l3_leaf_info["Uplink Interfaces"] != "" else None
		optional_params["bgp_as"] = int(l3_leaf_info[l3leaf.bgpAs]) if l3_leaf_info[l3leaf.bgpAs] != "" else None
		# optional_params["mlag_interfaces"] = [iface.strip() for iface in l3_leaf_info[l3leaf.mlagInterfaces].split(",") if iface] if l3_leaf_info[l3leaf.mlagInterfaces] != "" else None
		if ne("", l3_leaf_info[l3leaf.mlagInterfaces]):
			optional_params["mlag_interfaces"] = [iface.strip() for iface in l3_leaf_info[l3leaf.mlagInterfaces].split(",") if iface] if l3_leaf_info[l3leaf.mlagInterfaces] != "" else None
		else:
			optional_params["mlag"] = False
		


		for k, v in optional_params.items():
			if v is not None:
				v = int(v) if type(v) == float else v
				node_details[k] = v

		if l3_leaf_info[l3leaf.containerName] not in node_groups.keys():
			node_groups[l3_leaf_info[l3leaf.containerName]] = {"nodes": {hostname: node_details}}
		else:
			node_groups[l3_leaf_info[l3leaf.containerName]]["nodes"][hostname] = node_details

	# print(yaml.dump(node_groups))
	#parse default values
	l3_defaults_worksheet = workbook.sheet_by_name(l3leafDetail.sheetName)
	defaults = {}
	bgp_defaults = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, l3_defaults_worksheet.nrows):
		k, v = l3_defaults_worksheet.cell_value(row,0), l3_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys() and v is not None and v != "":
			v = convertToList(k, v, "L3")
			v = convertToBoolIfNeeded(v)
			v = int(v) if type(v) == float else v
			defaults[configuration_variable_mappers[k]] = v

	# defaults["uplink_interfaces"] = [interface.strip() for interface in defaults["uplink_interfaces"].split(",") if interface] if defaults["uplink_interfaces"] != "" else None

	# defaults["uplink_switches"] = [switchs.strip() for switchs in defaults["uplink_switches"].split(",") if switchs] if defaults["uplink_switches"] != "" else None

	# print(json.dumps(defaults, indent=2))
	l3_yaml["defaults"] = defaults
	l3_yaml["node_groups"] = consolidateNodeGroups(node_groups)
	
	# BGP default 세팅
	l3_yaml["defaults"]["bgp_defaults"] = parseLeafBGPDefaults(inventory_file)


	return l3_yaml

def parseL3LeafBGPDefaults(inventory_file):
	#parse default values
	l3leafDetail = L3LeafDetail()
	configuration_variable_mappers = {"BGP wait-install": "wait_install", "BGP distance setting":"distance_setting", "BGP default ipv4-unicast": "ipv4_unicast"}
	l3_leaf_info = {}
	workbook = xlrd.open_workbook(inventory_file)
	l3_defaults_worksheet = workbook.sheet_by_name(l3leafDetail.sheetName)
	bgp_defaults = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, l3_defaults_worksheet.nrows):
		k, v = l3_defaults_worksheet.cell_value(row,0), l3_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys() and v is not None and v != "":
			v = convertToBoolIfNeeded(v)
			bgp_defaults[configuration_variable_mappers[k]] = v
	bgp_defaults_list = []
	config_values = {
		"wait_install":
			{
				True: "update wait-install",
				False: None
			},
		"ipv4_unicast":
		{
			True: "bgp default ipv4-unicast",
			False: "no bgp default ipv4-unicast"
		}
	}
	for k, v in bgp_defaults.items():
		if k in config_values.keys():
			v = config_values[k][bool(v)]
		if v is not None:
			bgp_defaults_list.append(v)
	return bgp_defaults_list

# Super Spine Switches
def parseSuperSpineInfo(inventory_file):
	spine = Spine()
	spineDetail = SpineDetail()
	spine_yaml = {"nodes": {}}

	configuration_variable_mappers = {
		spine.platform: "platform", 
		spine.bgpPeeringAsnRange: "leaf_as_range", 
		spine.bgpAsn:"bgp_as",
		spine.loopbackIpv4Pool: "loopback_ipv4_pool",
		spine.mlagPeerIpv4Pool: "mlag_peer_ipv4_pool",
		spine.mlagPeerL3Ipv4Pool: "mlag_peer_l3_ipv4_pool",
		spine.uplinkSwitches: "uplink_switches",
		spine.uplinkSwitchInterfaces: "uplink_switch_interfaces",
		spine.uplinkInterfaces: "uplink_interfaces",
		spine.superSpine: "super_spine"
	}
	
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name(spine.sheetName)
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		spine_info = {}
		for col in range(inventory_worksheet.ncols):  			
			spine_info[first_row[col]]=inventory_worksheet.cell_value(row,col)

		if convertToBoolIfNeeded(spine_info[spine.superSpine]):				
			hostname = spine_info[spine.hostname]
			node_details = {}
			node_details["id"] = int(spine_info[spine.id])
			node_details["mgmt_ip"] = spine_info[spine.managementIp]
			node_details["super_spine_loopback_network_summary"] = "192.168.255.0/24"
			spine_yaml["nodes"][hostname] = node_details
			
	return spine_yaml

# Spine Switches
def parseSpineInfo(inventory_file):
	spine = Spine()
	spineDetail = SpineDetail()
	spine_yaml = {"defaults": {}, "nodes": {}}

	configuration_variable_mappers = {
		spine.platform: "platform", 
		spine.bgpPeeringAsnRange: "leaf_as_range", 
		spine.bgpAsn:"bgp_as",
		spine.loopbackIpv4Pool: "loopback_ipv4_pool",
		spine.mlagPeerIpv4Pool: "mlag_peer_ipv4_pool",
		spine.mlagPeerL3Ipv4Pool: "mlag_peer_l3_ipv4_pool",
		spine.uplinkSwitches: "uplink_switches",
		spine.uplinkSwitchInterfaces: "uplink_switch_interfaces",
		spine.uplinkInterfaces: "uplink_interfaces",
		spine.superSpine: "super_spine",
		spine.peerFilterName: "peer_filter_name",
		spine.peerFilterSequenceNumber: "peer_filter_sequence_number",
		spine.peerFilterMatch: "peer_filter_match",
		spine.prefixName: "prefix_name",
		spine.prefixSequenceNumber: "prefix_sequence_number",
		spine.prefixAction: "prefix_action",
		spine.routeMapName: "route_map_name",
		spine.routeMapType: "route_map_type",
		spine.routeMapSequence: "route_map_sequence",
		spine.routeMapMatch: "route_map_match"
	}
	
	workbook = xlrd.open_workbook(inventory_file)
	inventory_worksheet = workbook.sheet_by_name(spine.sheetName)
	node_groups = {}
	first_row = [] # The row where we stock the name of the column
	for col in range(inventory_worksheet.ncols):
		first_row.append( inventory_worksheet.cell_value(0,col) )
	# transform the workbook to a list of dictionaries
	for row in range(1, inventory_worksheet.nrows):
		spine_info = {}
		for col in range(inventory_worksheet.ncols):
			spine_info[first_row[col]]=inventory_worksheet.cell_value(row,col)

		# if not convertToBoolIfNeeded(spine_info[spine.superSpine]):				
		hostname = spine_info[spine.hostname]
		node_details = {}
		node_details["id"] = int(spine_info[spine.id])
		node_details["mgmt_ip"] = spine_info[spine.managementIp]

		# if ne(spine_info[spine.uplinkSwitches], ""):
		# 	node_details["uplink_switches"] = [swtich.strip() for swtich in spine_info[spine.uplinkSwitches].split(",")]
		
		# if ne(spine_info[spine.uplinkSwitchInterfaces], ""):
		# 	node_details["uplink_switch_interfaces"] = [swtich.strip() for swtich in spine_info[spine.uplinkSwitchInterfaces].split(",")]
		
		# if ne(spine_info[spine.uplinkInterfaces], ""):
		# 	node_details["uplink_interfaces"] = [swtich.strip() for swtich in spine_info[spine.uplinkInterfaces].split(",")]

		spine_yaml["nodes"][hostname] = node_details
		
	#parse default values
	spine_defaults_worksheet = workbook.sheet_by_name(spineDetail.sheetName)
	# transform the workbook to a list of dictionaries
	for row in range(1, spine_defaults_worksheet.nrows):
			k, v = spine_defaults_worksheet.cell_value(row,0), spine_defaults_worksheet.cell_value(row,1)
			if k in configuration_variable_mappers.keys() and v is not None and v != "":
				v = convertToBoolIfNeeded(v)
				v = int(v) if type(v) == float else v
				spine_yaml["defaults"][configuration_variable_mappers[k]] = v

	##### Peer Filter 처리 S #####
	if ne("", spine_yaml["defaults"]["peer_filter_name"]) and ne("", spine_yaml["defaults"]["peer_filter_sequence_number"]) and ne("", spine_yaml["defaults"]["peer_filter_match"]):
		spine_yaml["defaults"]["peer_filters"] = [{
				"name" : spine_yaml["defaults"]["peer_filter_name"],
				"sequence_numbers" : [{
					"sequence": spine_yaml["defaults"]["peer_filter_sequence_number"],
					"match": spine_yaml["defaults"]["peer_filter_match"]
				}]
			}]
		
	del(spine_yaml["defaults"]["peer_filter_name"])
	del(spine_yaml["defaults"]["peer_filter_sequence_number"])
	del(spine_yaml["defaults"]["peer_filter_match"])
	##### Peer Filter 처리 E #####

	##### Prefix 처리 S #####
	if ne("", spine_yaml["defaults"]["prefix_name"]) and ne("", spine_yaml["defaults"]["prefix_sequence_number"]) and ne("", spine_yaml["defaults"]["prefix_action"]):
		spine_yaml["defaults"]["prefix_lists"] = [{
				"name" : spine_yaml["defaults"]["prefix_name"],
				"sequence_numbers" : [{
					"sequence": spine_yaml["defaults"]["prefix_sequence_number"],
					"action": spine_yaml["defaults"]["prefix_action"]
				}]
			}]
	del(spine_yaml["defaults"]["prefix_name"])
	del(spine_yaml["defaults"]["prefix_sequence_number"])
	del(spine_yaml["defaults"]["prefix_action"])
	##### Prefix 처리 E #####

	##### Route Map 처리 S #####
	if ne("", spine_yaml["defaults"]["route_map_name"]) and ne("", spine_yaml["defaults"]["route_map_type"]) and ne("", spine_yaml["defaults"]["route_map_sequence"]) and ne("", spine_yaml["defaults"]["route_map_match"]):
		spine_yaml["defaults"]["route_maps"] = [{
				"name" : spine_yaml["defaults"]["route_map_name"],
				"sequence_numbers" : [{
					"sequence": spine_yaml["defaults"]["route_map_sequence"],
					"type": spine_yaml["defaults"]["route_map_type"],
					"match": [spine_yaml["defaults"]["route_map_match"]]
				}]
			}]
	del(spine_yaml["defaults"]["route_map_name"])
	del(spine_yaml["defaults"]["route_map_type"])
	del(spine_yaml["defaults"]["route_map_sequence"])
	del(spine_yaml["defaults"]["route_map_match"])
	##### Route Map E #####

	spine_yaml["defaults"]["bgp_defaults"] = parseSpineBGPDefaults(inventory_file)

	return spine_yaml

def parseLeafBGPDefaults(inventory_file):
  #parse default values
	# BGP default 세팅
	l3leafDetail = L3LeafDetail()
	configuration_variable_mappers = {
		l3leafDetail.bgpDistanceSetting: "bgp_distance_setting",
		l3leafDetail.bgpDefaultIpv4Unicast: "bgp_default_ipv4_unicast",
		l3leafDetail.bgpGracefulRestartTime: "bgp_graceful_restart_time",
		l3leafDetail.bgpGracefulRestart: "bgp_graceful_restart"
	}
	workbook = xlrd.open_workbook(inventory_file)
	spine_defaults_worksheet = workbook.sheet_by_name(l3leafDetail.sheetName)
	bgp_defaults = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, spine_defaults_worksheet.nrows):
		k, v = spine_defaults_worksheet.cell_value(row,0), spine_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys() and v is not None and v != "":
			v = convertToBoolIfNeeded(v)
			bgp_defaults[configuration_variable_mappers[k]] = v

			if eq(l3leafDetail.bgpGracefulRestartTime, k):
				# print("graceful-restart restart-time !!")
				v = bgp_defaults[configuration_variable_mappers[k]]
				v = int(v) if type(v) == float else v
				v = str(v)
				bgp_defaults[configuration_variable_mappers[k]] = "graceful-restart restart-time " + v

	
	bgp_defaults_list = []
	config_values = {
		"bgp_default_ipv4_unicast":
			{
				True: "bgp default ipv4-unicast",
				False: "no bgp default ipv4-unicast"
			},
		"bgp_graceful_restart":
			{
				True: "graceful-restart",
				False: None
			}
	}

	for k, v in bgp_defaults.items():
		if k in config_values.keys():
			v = config_values[k][bool(v)]
		if v is not None:
			bgp_defaults_list.append(v)
			
	return bgp_defaults_list

def parseSpineBGPDefaults(inventory_file):
	#parse default values
	spineDetail = SpineDetail()
	configuration_variable_mappers = {
		spineDetail.bgpWaitForConvergence:"update_wait_for_convergence", 
		spineDetail.bgpWaitInstall: "wait_install", 
		spineDetail.bgpDistanceSetting:"distance_setting", 
		spineDetail.bgpDefaultIpv4Unicast: "ipv4_unicast",
	}
	workbook = xlrd.open_workbook(inventory_file)
	spine_defaults_worksheet = workbook.sheet_by_name(spineDetail.sheetName)
	bgp_defaults = {}
	# transform the workbook to a list of dictionaries
	for row in range(1, spine_defaults_worksheet.nrows):
		k, v = spine_defaults_worksheet.cell_value(row,0), spine_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys() and v is not None and v != "":
			v = convertToBoolIfNeeded(v)
			bgp_defaults[configuration_variable_mappers[k]] = v
	bgp_defaults_list = []
	config_values = {
		"update_wait_for_convergence":
			{
				True: "update wait-for-convergence",
				False: None
			},
		"wait_install":
			{
				True: "update wait-install",
				False: None
			},
		"ipv4_unicast":
		{
			True: "bgp default ipv4-unicast",
			False: "no bgp default ipv4-unicast"
		}
	}
	for k, v in bgp_defaults.items():
		if k in config_values.keys():
			v = config_values[k][bool(v)]
		if v is not None:
			bgp_defaults_list.append(v)
	return bgp_defaults_list

def parseGeneralVariables(inventory_file):
	genernalConfiguration = GenernalConfiguration()
	general_yaml = {}
	configuration_variable_mappers = {
		genernalConfiguration.fabricName: "fabric_name",
		genernalConfiguration.mlagIgpPeerNetworkSummary: "leaf_peer_l3",
		genernalConfiguration.mlagPeerNetworkSummary: "mlag_peer",
		genernalConfiguration.vxlanVlanAwareBundles: "vxlan_vlan_aware_bundles",
		genernalConfiguration.pointToPointUplinkMtu: "p2p_uplinks_mtu",
		genernalConfiguration.bgpIpv4UnderlayPeerGroupName: "bgp_ipv4_name",
		genernalConfiguration.bgpIpv4UnderlayPeerGroupPassword: "bgp_ipv4_password",
		genernalConfiguration.bgpIpv4UnderlayPeerFilter: "bgp_ipv4_filter",
		genernalConfiguration.bgpIpv4UnderlayPrefix: "bgp_ipv4_prefix",
		genernalConfiguration.bgpEvpnOverlayPeerGroupName: "bgp_evpn_name",
		genernalConfiguration.bgpEvpnOverlayPeerGroupPassword: "bgp_evpn_password",
		genernalConfiguration.bgpMlagIpv4UnderlayGroupPassword: "bgp_mlag_ipv4_password",
		genernalConfiguration.bgpBfdMultihopInterval: "bfd_interval",
		genernalConfiguration.bgpBfdMultihopMinRx: "bfd_min_rx",
		genernalConfiguration.bgpBfdMultihopMultiplier: "bfd_multiplier"
	}
	#parse default values
	workbook = xlrd.open_workbook(inventory_file)
	general_defaults_worksheet = workbook.sheet_by_name(genernalConfiguration.sheetName)
	# transform the workbook to a list of dictionaries
	for row in range(1, general_defaults_worksheet.nrows):
		k, v = general_defaults_worksheet.cell_value(row,0), general_defaults_worksheet.cell_value(row,1)
		if k in configuration_variable_mappers.keys():
			v = convertToBoolIfNeeded(v)
			v = v if v != "" else None
			v = int(v) if type(v) == float else v

			if (eq(k, genernalConfiguration.fabricName)):
				v = v + "_FABRIC"

			general_yaml[configuration_variable_mappers[k]] = v

	# general_yaml["bgp_peer_groups"] = {
	# 	"IPv4_UNDERLAY_PEERS":{"password": general_yaml["bgp_ipv4_password"]},
	# 	"EVPN_OVERLAY_PEERS":{"password": general_yaml["bgp_evpn_password"]},
	# 	"MLAG_IPv4_UNDERLAY_PEER":{"password": general_yaml["bgp_mlag_ipv4_password"]}
	# }

	general_yaml["bgp_peer_groups"] = {
		"IPv4_UNDERLAY_PEERS":{ "name": general_yaml["bgp_ipv4_name"], "bgp_listen_range_prefix": general_yaml["bgp_ipv4_prefix"], "peer_filter": general_yaml["bgp_ipv4_filter"], "password": general_yaml["bgp_ipv4_password"]},
		"EVPN_OVERLAY_PEERS":{ "name": general_yaml["bgp_evpn_name"], "password": general_yaml["bgp_evpn_password"]}
	}

	del(general_yaml["bgp_ipv4_password"])
	del(general_yaml["bgp_evpn_password"])
	# del(general_yaml["bgp_mlag_ipv4_password"])

	# general_yaml["mlag_ips"] = {
	# 	"leaf_peer_l3": general_yaml["leaf_peer_l3"], 
	# 	"mlag_peer": general_yaml["mlag_peer"]
	# }

	# del(general_yaml["leaf_peer_l3"])
	# del(general_yaml["mlag_peer"])

	general_yaml["bfd_multihop"] = {
		"interval": general_yaml["bfd_interval"], 
		"min_rx": general_yaml["bfd_min_rx"], 
		"multiplier": general_yaml["bfd_multiplier"]
	}

	del(general_yaml["bfd_interval"])
	del(general_yaml["bfd_min_rx"])
	del(general_yaml["bfd_multiplier"])

	return general_yaml

def generateGroupVarsFabric(file_location):

	fabric_name = parseGeneralVariables(file_location)
	# fabric_name["super_spine"] = parseSuperSpineInfo(file_location)
	fabric_name["spine"] = parseSpineInfo(file_location)
	fabric_name["l3leaf"] = parseL3LeafInfo(file_location)
	fabric_name["l2leaf"] = parseL2LeafInfo(file_location)
	fabric_name["leaf_bgp_defaults"] = parseL3LeafBGPDefaults(file_location)

	return fabric_name
