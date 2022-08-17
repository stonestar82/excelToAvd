# -*- coding: utf-8 -*-
#!/usr/bin/env python
from ast import Raise
import json, collections, pprint
from operator import ne, eq
from datetime import datetime, timedelta
from netmiko import ConnectHandler
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

def taskPrint(task):
  task = task + " "
  print(task.ljust(100, "*") + "\n")

def main():
  with open("switchInit.json", "r") as f:
    config = json.load(f)
    f.close()

  url = config["url"]
  totalSpineCount = config["spineCount"]
  totalLeafCount = config["leafCount"]
  definedSpineSysmac = config["definedSpineSysmac"]
  ansibleId = config["ansibleId"]
  ansiblePw = config["ansiblePw"]
  
  spines = []
  leafs = []

  ##### defined Spine 검색 S #####
  definedSpineIp = None
  taskPrint("TASK [Defined Spine 검색]")
  with open("./upload/123456789", "r") as f:
    switchs = f.readlines()
    f.close()
  
  for swtich in switchs:
    tmp = swtich.split("|")
    # print("tmp = ", tmp, swtich)
    ip = tmp[0].strip()
    sysmac = tmp[1].strip()
    
    if eq(definedSpineSysmac, sysmac):
      print("Defined Spine 확인, IP = ", ip)
      definedSpineIp = ip
      break
    
  if not definedSpineIp:
    print("Defined Spine이 없습니다.")
    exit()
  ##### defined Spine 검색 E #####
    
  ##### defined Spine LLDP로 leaf 확인 S #####
  taskPrint("TASK [Leaf 검색]")
  connect = ConnectHandler(
    device_type = "arista_eos",
    host = definedSpineIp,
    username = ansibleId,
    password = ansiblePw
  )  
  connect.enable()
  
  data = json.loads(connect.send_command("show lldp neighbors detail | json", ))["lldpNeighbors"]
  
  connect.disconnect()
  
  ## Ethernet1, Ethernet2, Ethernet3... 순으로 정렬 처리
  sortedData = collections.OrderedDict(sorted(data.items()))
  
  for neighbor in sortedData:
    ## Management는 제외
    if not neighbor.startswith("Management") and sortedData[neighbor]["lldpNeighborInfo"]:
      leafs.append({"ip": sortedData[neighbor]["lldpNeighborInfo"][0]["managementAddresses"][0]["address"]})

  # print(leafs)
  if ne(len(leafs), totalLeafCount):
    print("!!!!! leaf 갯수가 일치하지 않습니다 !!!!!")
    print("total leaf count = ", totalLeafCount, " 확인된 leaf 수 = ", len(leafs))
  ##### defined Spine LLDP로 leaf 확인 E #####

  ##### leaf-1 lldp 로 spine 체크 S #####
  connect = ConnectHandler(
    device_type = "arista_eos",
    host = leafs[0]["ip"],
    username = ansibleId,
    password = ansiblePw
  )  
  connect.enable()
  
  data = json.loads(connect.send_command("show lldp neighbors detail | json", ))["lldpNeighbors"]
  
  connect.disconnect()
  
  ## Ethernet1, Ethernet2, Ethernet3... 순으로 정렬 처리
  sortedData = collections.OrderedDict(sorted(data.items()))
  
  for neighbor in sortedData:
    ## Management는 제외
    if not neighbor.startswith("Management") and sortedData[neighbor]["lldpNeighborInfo"]:
      spines.append({"ip": sortedData[neighbor]["lldpNeighborInfo"][0]["managementAddresses"][0]["address"]})

  # print(leafs)
  if ne(len(spines), totalSpineCount):
    print("!!!!! spine 갯수가 일치하지 않습니다 !!!!!")
    print("total spine count = ", totalSpineCount, " 확인된 spine 수 = ", len(spines))
  
  ##### leaf-1 lldp 로 spine 체크 E #####
  
  ###### spine, leaf config 다운로드 S #####
  ## config 파일 다운로드전 체크
  idx = 0
  for spine in spines:   
    idx += 1
    fileName = "Spine-0" + str(idx)
    try:
      res = urlopen(url + "/cfgs/" + fileName)
    except HTTPError as e:
      print("config 파일이 없습니다.") ## 404
      print(url + "/cfgs/" + fileName) ## 404
      exit()
    
    connect = ConnectHandler(
      device_type = "arista_eos",
      host = spine["ip"],
      username = ansibleId,
      password = ansiblePw
    )
    connect.enable()
  
    cmd = "bash sudo wget " + url + "/cfgs/" + fileName + " -O /mnt/flash/startup-config"
    connect.send_command(cmd)
    print(fileName + " config ok")
    
  ## config 파일 다운로드전 체크
  idx = 0
  for leaf in leafs:   
    idx += 1
    fileName = "Leaf-0" + str(idx)
    try:
      res = urlopen(url + "/cfgs/" + fileName)
    except HTTPError as e:
      print("config 파일이 없습니다.") ## 404
      print(url + "/cfgs/" + fileName) ## 404
      exit()
    
    connect = ConnectHandler(
      device_type = "arista_eos",
      host = leaf["ip"],
      username = ansibleId,
      password = ansiblePw
    )
    connect.enable()
  
    cmd = "bash sudo wget " + url + "/cfgs/" + fileName + " -O /mnt/flash/startup-config"
    connect.send_command(cmd)
    print(fileName + " config ok")


  ###### spine, leaf config 다운로드 E #####
  taskPrint("TASK [End]")

if __name__ == '__main__':
  main()