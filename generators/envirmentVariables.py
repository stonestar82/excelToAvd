## Management Interface
MGMT_INTERFACE = "Management1"
MGMT_INTERFACE_VRF = "MGMT"


## Group vars all.yml
GROUP_VARS_ALL_CONFIG = """
# AVD configurations variables

## terminal length 40
terminal:
  length: 40

## service routing protocols model multi-agent
service_routing_protocols_model: multi-agent

## spanning-tree mode mstp
spanning_tree:
  mode: mstp

## clock timezone Asia/Seoul
clock:
  timezone: Asia/Seoul

## ip routing
ip_routing: True

## vrf
vrfs:
- name: MGMT
  ip_routing: False

## banner login
banners:
  login: "***********************************************************************\\nGlobalTelecom and Arista Networks\\n***********************************************************************\\nEOF"
"""

# ## ansible.cfg
# ANSIBLE_CONFIG = '''[defaults]
# host_key_checking = False
# inventory =./inventory/inventory.yml
# gathering = explicit
# retry_files_enabled = False
# # filter_plugins = ansible-avd/plugins/filters
# # roles_path = ansible-avd/roles
# # library = ansible-avd/library
# collections_paths = /media/sf_workspace/avdCloudvisionDemo/.ansible/collections/ansible_collections
# action_plugins = /usr/lib/python2.7/site-packages/napalm_ansible/plugins/action
# jinja2_extensions =  jinja2.ext.loopcontrols,jinja2.ext.do,jinja2.ext.i18n
# # enable the YAML callback plugin.
# stdout_callback = yaml
# # enable the stdout_callback when running ad-hoc commands.
# bin_ansible_callbacks = True
# command_warnings=False
# deprecation_warnings=False
# forks = 100

# [persistent_connection]
# connect_timeout = 120
# command_timeout = 120'''