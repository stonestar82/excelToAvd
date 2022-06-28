class L3LeafDetail():
  """
  l3 leaf detail domain 2022.06.27 pks
  """
  def __init__(self):
    # sheet name
    self.sheetName = "L3 Leaf Configuration Details"

    # column name
    self.platform = "Platform"
    self.loopbackIpv4Pool = "Loopback IPv4 Pool"
    self.loopbackIpv4Offset = "Loopback IPv4 Offset"
    self.vtepLoopbackIpv4Pool = "VTEP Loopback IPv4 Pool"
    self.uplinkInterfaces = "Uplink Interfaces"
    self.uplinkSwitches = "Uplink Switches"
    self.uplinkIpv4Pool = "Uplink IPv4 Pool"
    self.mlagInterfaces = "MLAG Interfaces"
    self.mlagPeerIpv4Pool = "MLAG Peer IPv4 Pool"
    self.mlagPeerL3Ipv4Pool = "MLAG Peer L3 IPv4 Pool"
    self.virtualRouterMacAddress = "Virtual Router Mac-Address"
    self.spanningTreeMode = "Spanning-tree Mode"
    self.spanningTreePriority = "Spanning-tree Priority"
    self.bgpWaitInstall = "BGP wait-install"
    self.bgpDistanceSetting = "BGP distance setting"
    self.bgpDefaultIpv4Unicast = "BGP default ipv4-unicast"
    self.bgpGracefulRestartTime = "BGP Graceful Restart Time"
    self.bgpGracefulRestart = "BGP Graceful Restart"