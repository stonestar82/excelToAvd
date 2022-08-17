from ast import Raise
from src.domain.Switch import *
from netmiko import ConnectHandler
from netmiko import SSHDetect
from operator import eq, ne
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

class SwitchIdentification():

  def __init__(self, switch):
    self.switch = switch

  ## 스위치에 접속
  def switchConnect(self):
    reomote = {
      "device_type": "autodetect",
      "host": self.switch.ip,
      "username": self.switch.user,
      "password": self.switch.password
    }
    
    guesser = SSHDetect(**reomote)
    best_match = guesser.autodetect()

    print(best_match)
    
    self.connect = ConnectHandler(**reomote)
    
    print("ip = ", self.switch.ip)

    self.connect.enable()
  

  ## 스위치 spine, leaf 판별
  def identification(self, totalLeafCount):
    
    data = self.lldpScan()
    neighbors = 0
    neighborsMac = []    

    for k in data.get("lldpNeighbors"):
      item = data.get("lldpNeighbors").get(k)
      if item["lldpNeighborInfo"]:
        neighbors = neighbors + 1
        neighborsMac.append(item["lldpNeighborInfo"][0].get("chassisId", ""))
    
    ## 중복 mac 제거
    neighborsMac = list(set(neighborsMac))      
    self.switch.mlacExist = "y" if ne(neighbors, len(neighborsMac)) else "n"

    ## mlac(or portchannell ??)이 존재하면 neighbers - mlac 포트수
    if eq(self.switch.mlacExist, "y"):
      neighbors = neighbors - 1 - (neighbors - len(neighborsMac))

    self.switch.neighbors = neighbors

    self.switch.type = "spine" if eq(self.switch.neighbors, totalLeafCount) else "leaf"

    ## 스위치 순서 확인
    ## eth1포트 lldp의 포트에따라 정해진다. 
    lldpPort = data.get("lldpNeighbors").get("Ethernet1").get("lldpNeighborInfo")[0].get("neighborInterfaceInfo").get("interfaceId_v2").replace("Ethernet", "")
    # self.switch.hostname = self.switch.type.upper() + lldpPort
    if eq("spine", self.switch.type):
      self.switch.hostname = "Spine-0" + lldpPort
    else:
      self.switch.hostname = "Leaf-0" + lldpPort

  ## lldp 
  def lldpScan(self):
    data = self.connect.send_command("show lldp neighbors detail | json")

    return json.loads(data)

  ## config 다운로드
  def configDownload(self, url, fileName):
    
    ## config 파일 다운로드전 체크
    try:
      res = urlopen(url + "/cfgs/" + fileName)
      print(res.status)
    except HTTPError as e:
      err = e.read()
      code = e.getcode()    
      print("config 파일이 없습니다.") ## 404
      print(url + "/cfgs/" + fileName) ## 404
      exit()
    
    cmd1 = "cli vrf MGMT"
    cmd2 = "bash sudo wget " + url + "/cfgs/" + fileName + " -O /mnt/flash/startup-config"
    cmd = []
    # cmd.append(cmd1)
    # cmd.append(cmd2)
    
    # self.connect.send_command()
    # self.connect.send_config_set(cmd)
    self.connect.send_command("bash sudo wget " + url + "/cfgs/" + fileName + " -O /mnt/flash/startup-config")
    # self.connect.send_command("wr")

    print("bash sudo wget " + url + "/cfgs/" + fileName + " -O /mnt/flash/startup-config")

  ## reboot
  def reboot(self):
    self.connect.send_command("bash sudo shutdown -r 1")
    print("bash sudo shutdown -r 1")

  def disconnect(self):
    self.connect.disconnect()