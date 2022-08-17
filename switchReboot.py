# -*- coding: utf-8 -*-
#!/usr/bin/env python
import json
from netmiko import ConnectHandler

def taskPrint(task):
  task = task + " "
  print(task.ljust(100, "*") + "\n")

def main():
  with open("switchInit.json", "r") as f:
    config = json.load(f)
    f.close()
    
  ansibleId = config["ansibleId"]
  ansiblePw = config["ansiblePw"]
  
  ##### Swtich 재부팅 S #####
  taskPrint("TASK [Swtich 재부팅]")
  with open("./upload/123456789", "r") as f:
    switchs = f.readlines()
    f.close()
  
  for swtich in switchs:
    tmp = swtich.split("|")
    ip = tmp[0].strip()
    
    connect = ConnectHandler(
      device_type = "arista_eos",
      host = ip,
      username = ansibleId,
      password = ansiblePw
    )  
    connect.enable()
    connect.send_command("bash sudo shutdown -r 1")    
    connect.disconnect()
    
  ##### Swtich 재부팅 E #####
  taskPrint("TASK [End]")

if __name__ == '__main__':
  main()