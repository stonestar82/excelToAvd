class L2LeafDetail():
  """
  l2 leaf detail domain 2022.06.27 pks
  """
  def __init__(self):
    # sheet name    
    self.sheetName = "L2 Leaf Configuration Details"

    # column name
    self.platform = "Platform"
    self.uplinkSwitches = "Uplink Switches"
    self.uplinkInterfaces = "Uplink Interfaces"
    self.mlag = "MLAG"
    self.mlagInterfaces = "MLAG Interfaces"
    self.mlagPeerIpv4Pool = "MLAG Peer IPv4 Pool"
    self.mlagPeerL3Ipv4Pool = "MLAG Peer L3 IPv4 Pool"
    self.virtualRouterMacAddress = "Virtual Router Mac Address"
    self.spanningTreeMode = "Spanning-tree Mode"
    self.spanningTreePriority = "Spanning-tree Priority"