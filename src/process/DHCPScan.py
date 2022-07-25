import re
from datetime import datetime

class DHCPScan():

  def searchIp(self, txt):
    re_ip = re.search('[0-9]+(?:\.[0-9]+){3}', txt)
    
    ip = ""

    if re_ip:
      ip = re_ip.group()

    return ip


  def searchMac(self, txt):
    re_mac = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', txt)

    mac = ""

    if re_mac:
      mac = re_mac.group()
    
    return mac

  def searchTime(self, txt):
    re_mac = re.search(r'[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9]', txt)

    if re_mac:
      t = re_mac.group()

    return t