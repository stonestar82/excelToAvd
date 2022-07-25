from datetime import datetime
import os, sys
from rollbackCfg import rollback
from main import excellToYml
from operator import ne, eq

print("sys.argv = ", sys.argv)

jobTypes = ["config", "rollback"]
if len(sys.argv) < 2:
  print("tags값을 입력해 주세요")

else:
  nowDate = datetime.now().strftime("%Y%m%d%H%M%S")  
  tags = sys.argv[1]

  cmd = ""
  if len(sys.argv) >= 3:
    jobType = sys.argv[2]
    jobType.lower()

    if not jobType in jobTypes:
      print("작업타입은 config, rollback 입니다")
      exit()

    if eq("config", jobType):
      excellToYml()
      cmd = "ansible-playbook design.yml && ansible-playbook config.yml --tags=" + tags + "&& "
    elif eq("rollback", jobType):
      # print("rollback 실행")
      rollback(tags)

  cmd = cmd + "ansible-playbook deploy.yml -e 'nowDate=" + nowDate + "' --tags=" + tags
  # print(cmd)





  os.system(cmd)