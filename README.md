# AVD Excel Loader

1. 기본 프로젝트 https://github.com/arista-netdevops-community/excel-to-avd.git
2. 2년전 마지막 업데이트로 지금과 맞지 않음 (2022.06.28 기준)
3. ansible 및 각 라이브러리 설치된 환경에서 실행
 - inventory.xlsx 에 항목 기입후 avdExec(alias avdExec='python3 main.py') 실행
 - excell -> inventory, ansible playbook 생성 -> ansible playbook 실행


# 추가 설치 라이브러리
1. xlrd
  - 최신버전은 xlsx 파일을 지원하지 않아 2 버전 미만으로 설치
2. PyYAML
  - dict 형식의 데이터를 yaml 형식으로 변경해줌
