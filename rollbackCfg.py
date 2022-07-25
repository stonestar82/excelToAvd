from fileinput import filename
import os, sys, pprint, shutil
from operator import eq, ne



def main():
  rollbackPath = "./inventory/config_backup/pre/"
  configPath = "./inventory/intended/configs/"

  cfgFiles = os.listdir(rollbackPath)

  filePrefix = tags = sys.argv[1]

  ## cfg 파일리스트
  cfgFileList = {}
  for cfg in cfgFiles:
    ## 파일명 형식 p2pip_DC1-SPINE1_pre_20220722104810.cfg
    if cfg.startswith(filePrefix):
      d = cfg.split("_")
      s = len(d)
      fileName = "_".join(d[0:s-1])
      fileDate = str(d[s-1]).replace(".cfg", "")

      if not fileName in cfgFileList:
        cfgFileList.setdefault(fileName, fileDate)
      elif int(fileDate) > int(cfgFileList[fileName]):
          cfgFileList[fileName] = fileDate
            
  # pprint.pprint(cfgFileList)


  ## 파일 복사
  for cfg in cfgFileList:
    sourceFile = rollbackPath + cfg + "_" + cfgFileList[cfg] + ".cfg"
    destinationFile = configPath + str(cfg).replace(filePrefix + "_", "").replace("_pre", "") + ".cfg"
    # print(sourceFile, destinationFile)
    shutil.copyfile(sourceFile, destinationFile)

if __name__ == "__main__":
	main()