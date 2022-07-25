class Spine():
  """
  spine domain 2022.06.27 pks
  """
  def __init__(self):
    # sheet name
    self.sheetName = "Spine Info"
    self.detailSheetName = "Spine Configuration Details"

    # self.sheetName column name
    self.id = "ID"
    self.hostname = "Hostname"
    self.managementIp = "Management IP"
    self.superSpine = "Super Spine"

    # self.detailSheetName column name
    self.platform = "Platform"
    self.bgpAsn = "BGP ASN"
    self.bgpPeeringAsnRange = "BGP Peering ASN Range"
    self.bgpWaitInstall = "BGP wait-install"
    self.bgpWaitForConvergence = "BGP wait-for-convergence"
    self.bgpDistanceSetting = "BGP distance setting"
    self.bgpDefaultIpv4Unicast = "BGP default ipv4-unicast"
    self.loopbackIpv4Pool = "Loopback IPv4 Pool"
    self.mlagPeerIpv4Pool = "Mlag Peer IPv4 Pool"
    self.mlagPeerL3Ipv4Pool = "Mlag Peer L3 IPv4 Pool"
    self.uplinkSwitches = "Uplink Switches"
    self.uplinkSwitchInterfaces = "Uplink Switch Interfaces"
    self.uplinkInterfaces = "Uplink Interfaces"