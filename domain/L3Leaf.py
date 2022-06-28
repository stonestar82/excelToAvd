class L3Leaf():
  """
  l3 leaf domain 2022.06.27 pks
  """
  def __init__(self):
    # sheet name
    self.sheetName = "L3 Leaf Info"
    self.detailSheetName = "L3 Leaf Configuration Details"

    # self.sheetName column
    self.id = "ID"
    self.platform = "Platform"
    self.containerName = "Container Name"
    self.hostname = "Hostname"
    self.managementIp = "Management IP"
    self.mlagInterfaces = "MLAG Interfaces"
    self.bgpAs = "BGP AS"
    self.uplinkSwitchInterfaces = "Uplink Switch Interfaces"
    self.uplinkSwitches = "Uplink Switches"
    self.uplinkInterfaces = "Uplink Interfaces"
    self.remoteSpineInterfaces = "Remote Spine Interfaces"
    self.tenants = "Tenants"
    self.tags = "Tags"														
