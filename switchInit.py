# -*- coding: utf-8 -*-
from logging import exception
from src.process.SwitchIdentification import SwitchIdentification
from src.domain.Switch import Switch
import json
from operator import ne
from datetime import datetime, timedelta
from src.process.DHCPScan import DHCPScan

def taskPrint(task):
  task = task + " "
  print(task.ljust(100, "*") + "\n")


def main():
  with open("switchInit.json", "r") as f:
    config = json.load(f)

  url = config["url"]
  totalSpineCount = config["spineCount"]
  totalLeafCount = config["leafCount"]
  dhcpListPath = config["dhcpListPath"]
  ansibleId = config["ansibleId"]
  ansiblePw = config["ansiblePw"]

  # print(url, totalLeafCount, totalSpineCount, dhcpListPath, "|", ansibleId, ansiblePw)

  ##### dhcp 추출 S #####
  taskPrint("TASK [Start]")

  taskPrint("TASK [DHCP scan]")
  with open(dhcpListPath, "r") as f:
    now = datetime.now()
    scanSwitches = []
    dhcpScan = DHCPScan()
    
    data = f.read().split("lease")
    for line in data:
      ## ip 와 mac이 추출되면 end time 추출 및 현재 시간과 비교하여 유효분만 필터링
      ip = dhcpScan.searchIp(line)  
      mac = dhcpScan.searchMac(line)
      
      if ne("", ip) and ne("", mac):
        info = line.split(";")
        ## info[1] end time
        t = dhcpScan.searchTime(info[1])

        if ne("", t):
          endTime = datetime.strptime(t, "%Y/%m/%d %H:%M:%S")       
          dateDiff = now < endTime
          
          if dateDiff:
            obj = {"ip": ip, "mac": mac, "time":t}
            scanSwitches.append(obj)

  # print(scanSwitches)

  # tmpSwitch = ["192.168.22.240", "192.168.22.241", "192.168.22.243", "192.168.22.244", "192.168.22.245", "192.168.22.246"]

  ##### lldp 로 spine leaf 체크 및 config 파일 다운로드 S #####
  taskPrint("TASK [LLDP scan]")

  for item in scanSwitches:
      
    switch = Switch(item["ip"], "50:fa:80:e9:68:cf", "arista_eos")

    switch.user = ansibleId
    switch.password = ansiblePw   

    switchId = SwitchIdentification(switch)
    switchId.switchConnect()
    switchId.reboot()
    switchId.disconnect()

  ##### lldp 로 spine leaf 체크  및 config 파일 다운로드 E #####
  taskPrint("TASK [End]")

if __name__ == '__main__':
  main()