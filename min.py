# -*- coding: utf-8 -*-
# GlobalTelecom arista tools          # Test version : EOS-4.20.X, EOS-4.24.0F
# By kyoung wook min                  # Build version : v2020.06.17
# copy sftp:min@192.168.22.151/eosimage/py/min-20.06.17.py flash:
# show tech support : evpn 정보 추가
# import 모듈 변경     : from jsonrpclib import Server => from EapiClientLib import EapiClient
# peer ping  : vrf 별 /30 , /31
# auto descrtipin : lldp 이용 
# description lldp systemname 없는경우(익스트림), abbreviation try 추가
# description lldp vmware 정보 엇갈리는 부분 조정
# EVE-NG SerialNum 및 system mac address 생성 추가 create_serial()
# 
"""
alias gt bash python /mnt/flash/min-20.06.17.py %1
"""
import collections, time, sys, re, Ark, Logging, subprocess
from EapiClientLib import EapiClient

Ark.configureLogManager('GlobalTelecom')
Logging.logD( id="INFO_LOG", severity=Logging.logInfo, format="%s", explanation="This is a log message", recommendedAction="Just Informational log" )
switch = EapiClient(disableAaa=True, privLevel=15)

#### 포트의 lldp peer가 중복일 경우 제외할 인터페이스 - cvx 사용 port
except_list = ["Ma1","Ma0","Et1"]

#### 인터페이스 단축 명칭
int_dict = {'ethernet' : "Et", 'management': "Ma","port-channel" : "Po", "loopback" :"Lo","vlan" :"Vl",'eth' : "Et", 'x' : "X", 'gi' : "Gi",\
            'gigabitethernet' : "Gi",'te' : "Te",'tengigabitethernet' : "Te",'ten-gigabitethernet' : "Te",'m-gigabitethernet': "Ma",'vmnic': "Vn"}

def abbreviation(port_name, dict):
    try:
        portTemp = int(port_name)
        return port_name
    except:
        port_type = re.split('\d', port_name)[0]
        port_number = re.split('\D+', port_name, 1)[1]
        for key, val in dict.items():
            if port_type == key:
                return val + port_number
        return port_name

#### interface config
def int_config(int_num, config):
    i = "interface " + int_num
    switch.runCmds(1, ["configure", i, config])

#### print table
def print_table(list, dict ):
    list_maxlen  = [] ; format_str = "" ; total_len = 0 ; width = 2
    for y in list:
        z = []
        z.append(len(y))
        for x in dict.keys():
            z.append(len(str(dict[x][y])))
        list_maxlen.append(max(z))
    dict_maxlen = collections.OrderedDict(zip(list, list_maxlen))
    dict_title = collections.OrderedDict(zip(list, list))
    for key, val in dict_maxlen.items():
        format_str = format_str + "{p[" + key + "]:<" + str(val+width) + "}"
        total_len = total_len + (val+width)
    print " "
    print "="*total_len
    print " Arista - Globaltelecom ".center(total_len," ")
    print "="*total_len
    print format_str.format(p=dict_title)
    print "="*total_len
    for interface in dict.keys():
        print format_str.format(p=dict[interface])
    print "="*total_len

#    print "="*total_len/2-10 ,; print " Globaltelecom v1.0 ",; print "="*total_len/2-10
    print " "

#### peer ping
def peer_ping(cli_command , p ):
    dict_ping = collections.OrderedDict()
    list_ping = ["Name","Local_address","Peer_address","Result", "Mtu","Description","Vrf"]
    return_info = switch.runCmds( 1, [cli_command])
    return_info = return_info["result"]
    for interface in return_info[0]["interfaces"]:
        # 마스크를 이용한 수집 조건 설정
        mask_len = return_info[0]["interfaces"][interface]["interfaceAddress"]["primaryIp"]["maskLen"]
        if p in {"P","p"} and not mask_len in {30 , 31}:               #if mask_len != 30 and mask_len != 31 and mask_len != 24:
            continue
        else:
            if p == "pp" and mask_len in {0,32}:
                continue
        if not interface in dict_ping.keys():
            dict_ping[interface] = collections.OrderedDict(zip(list_ping, [''] * len(list_ping)))
            dict_ping[interface]["Mtu"] = return_info[0]["interfaces"][interface]["mtu"]
            dict_ping[interface]["Vrf"] = return_info[0]["interfaces"][interface]["vrf"]
            dict_ping[interface]["Description"] = return_info[0]["interfaces"][interface]["description"]

            # line protocol status 를 view 에서 제거 하기 위해서
            if return_info[0]["interfaces"][interface]["lineProtocolStatus"] != "up":
                dict_ping[interface]["Result"] = "Down"
            interfacename = return_info[0]["interfaces"][interface]["name"]
            #  "p" 일 경우 인터페이스명 단축
            if p == "p":
                interfacename = abbreviation(interfacename.lower(), int_dict)
            dict_ping[interface]["Name"] = interfacename
            # peer_address 계산
            local_addr = return_info[0]["interfaces"][interface]["interfaceAddress"]["primaryIp"]["address"]
            temp_addr = local_addr.split('.')
            if mask_len == 31:
                if int(temp_addr[3]) % 2 == 0:
                    temp_addr[3] = str(int(temp_addr[3]) + 1)
                else:
                    temp_addr[3] = str(int(temp_addr[3]) - 1)
            elif mask_len == 30:
                if int(temp_addr[3]) % 2 == 0:
                    temp_addr[3] = str(int(temp_addr[3]) - 1)
                else:
                    temp_addr[3] = str(int(temp_addr[3]) + 1)
            else:
                temp_addr = return_info[0]["interfaces"][interface]["interfaceAddress"]["broadcastAddress"].split('.')
            dict_ping[interface]["Peer_address"] = ".".join(temp_addr)
            dict_ping[interface]["Local_address"] = local_addr + "/" + str(mask_len)
    # ping check
    for interface in dict_ping.keys():
        if dict_ping[interface]["Result"] == "Down":
            continue
        return_info = switch.runCmds(1, ["enable", "ping vrf " + dict_ping[interface]["Vrf"] + " " + dict_ping[interface]["Peer_address"] + " source " + dict_ping[interface]["Name"] +" repeat 1"])
        return_info = return_info["result"]
    #    time.sleep(1)
        result = str(return_info[1]["messages"])
        if " 0% packet loss" in result:
            dict_ping[interface]["Result"] = "Pass"
        else:
            dict_ping[interface]["Result"] = "Fail"
    if p == "p":
        list_ping = ["Name", "Local_address", "Peer_address", "Result"]
    print_table(list_ping,collections.OrderedDict(sorted(dict_ping.items())))


#### lldp neighbor description
def lldp_description(cli_command, p ):
    dict_description = collections.OrderedDict()
    list_description = ["Name","Description","Counts"]
    return_info = switch.runCmds( 1, [cli_command])
    return_info = return_info["result"]
    prefix_str  = "description "
    connect_str = "_"
    for interface in return_info[0]["lldpNeighbors"]:
        detect_count = len(return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"])
        int_description = []
        if detect_count == 0:
            continue
        for i in range(detect_count):
            interfaceId = ''
    #        interfaceIdType = ''
            chassisId = ''
            chassisIdType = ''
            systemName = ''
            try:
                interfaceId     = return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["neighborInterfaceInfo"]["interfaceId"]
    #            interfaceIdType = return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["neighborInterfaceInfo"]["interfaceIdType"]
                chassisId       = return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["chassisId"]
                chassisIdType   = return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["chassisIdType"]
                systemName      = return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["systemName"]
                interfaceDescription = ""
                # systemName 이 없으면 제외 ( interfaceIdType 과 chassisIdType 둘다 mac address 인 경우 systemName 이 안나오는것 같음 )
                # extream 은 기본적으로 systemname 이 없음, 별도 설정 필요
            except:
                continue
            if not systemName:
                continue
            else:
                systemName = systemName.split(".")[0]  # domain 제외
                # VMware host -  vmnic 이 chassisid 에 나타남, 주니퍼 - interfaceIdType 이 Locally assigned 이면서 systemName 이 있고 interfaceId 는 숫자
                # 일반적인 경우 interfaceIdType은 interfaceName 이지만, vmware 는 chassisIdType 가 interfaceName 임
                if chassisIdType == "interfaceName":
                    interfaceId, chassisId = chassisId, interfaceId    # vmware 의 경우 값을 교체 함
                    m = re.search("on dvSwitch (\S+) \(etherswitch\)", return_info[0]["lldpNeighbors"][interface]["lldpNeighborInfo"][i]["neighborInterfaceInfo"]["interfaceDescription"])
                    if m and p in {"d","dd","dD"}:
                        systemName = systemName + "(" + m.group(1) + ")" # vmware 가상스위치 네임 추가
                interfaceId = interfaceId.split('\"')[1]                    # lldp에 intid 의 양끝 '\' 표시 제거
                interfaceId = abbreviation(interfaceId.lower(), int_dict)   # description에 사용하기 위해 인터페이스 명 단축

                if p in {"d","dd","dD"} and detect_count > 1 and interfaceId in except_list:
                    continue
                if not interface in dict_description.keys():
                    dict_description[interface] = collections.OrderedDict(zip(list_description, [''] * len(list_description)))
                    dict_description[interface]["Name"] = interface
                    dict_description[interface]["Counts"] = detect_count
                int_description.append(systemName + connect_str + interfaceId)

        if not int_description:
            continue
        if p in {"dD","DD","D"}:
            dict_description[interface]["Description"] = ",".join(sorted(int_description, reverse=True)).upper()
        else:
            dict_description[interface]["Description"] = ",".join(sorted(int_description, reverse=True)).lower()

        # 포트 채널 멤버 확인
        cli_command2 = "show interfaces " + interface
        return_info_po = switch.runCmds(1, [cli_command2])
        return_info_po = return_info_po["result"]
        try:
            m = re.search("Member of (Port-Channel\d+)", return_info_po[0]["interfaces"][interface]["interfaceMembership"])
            if m:
#                if not m.group(1) in dict_description.keys():
                dict_description[m.group(1)] = collections.OrderedDict(zip(list_description, [''] * len(list_description)))
                dict_description[m.group(1)]["Name"] = m.group(1)
                dict_description[m.group(1)]["Description"] = dict_description[interface]["Description"]
        except:
            continue

    # d 와 D 조합의 모든 옵션에 대한 결과를 표로 보여줌
    print_table(list_description, collections.OrderedDict(sorted(dict_description.items())))

    # 옵션이 두 글자의 경우 실행까지 포함됨
    if p in {"dd","dD","Dd","DD"}:
        for x in dict_description:
            int_config(dict_description[x]["Name"], prefix_str + dict_description[x]["Description"])
        Logging.log(INFO_LOG, "Complete Description Settings ")

def arista_support():

    subprocess.call('echo ========= mkdir /mnt/flash/support', shell=True)
    subprocess.call('sudo mkdir /mnt/flash/support', shell=True)
    subprocess.call('echo ==[1/5]== show tech-support', shell=True)
    subprocess.call("FastCli -p15 -c 'show tech-support | cat > /mnt/flash/support/1.tech-support-$HOSTNAME.log'", shell=True)
    subprocess.call('echo ==[2/5]== show logging system', shell=True)
    subprocess.call("FastCli -p15 -c 'show logging system | cat > /mnt/flash/support/2.logg-system-$HOSTNAME.log'", shell=True)
    subprocess.call('echo ==[3/5]== show agent log', shell=True)
    subprocess.call("FastCli -p15 -c 'show agent log | cat > /mnt/flash/support/3.agent-log-$HOSTNAME.log'", shell=True)
    subprocess.call('echo ==[4/5]== show agent qtrace', shell=True)
    subprocess.call("FastCli -p15 -c 'show agent qtrace | cat > /mnt/flash/support/4.agent-qtrace-$HOSTNAME.log'", shell=True)
    subprocess.call('echo ==[5/5]== show tech extended evpn', shell=True)
    subprocess.call("FastCli -p15 -c 'show tech extended evpn | cat > /mnt/flash/support/5.extended-evpn-$HOSTNAME.log'", shell=True)

    print ("Check cvx server")
    cvxcheck = subprocess.check_output ("FastCli -p15 -c 'show cvx'", shell=True )
    if "Status:" and "Enabled" in cvxcheck:
        print ("The cvx server is active and collects additional data. ")
        subprocess.call('echo ==[1/7]== show hsc status detail', shell=True)
        subprocess.call("FastCli -p15 -c 'show hsc status detail | cat > /mnt/flash/support/5.hsc-status-detail-$HOSTNAME.log'", shell=True)
        subprocess.call('echo ==[2/7]== show hsc status ovsdb', shell=True)
        subprocess.call("FastCli -p15 -c 'show hsc status ovsdb | cat > /mnt/flash/support/6.hsc-status-ovsdb-$HOSTNAME.log'", shell=True)
        subprocess.call('echo ==[3/7]== show hsc status ovsdb detail', shell=True)
        subprocess.call("FastCli -p15 -c 'show hsc status ovsdb detail | cat > /mnt/flash/support/7.hsc-status-ovsdb-detail-$HOSTNAME.log'", shell=True)
        subprocess.call('echo ==[4/7]== show hsc detail', shell=True)
        subprocess.call("FastCli -p15 -c 'show hsc detail | cat > /mnt/flash/support/8.hsc-detail-$HOSTNAME.log'", shell=True)
        subprocess.call('echo ==[5/7]== show hsc detail ovsdb', shell=True)
        subprocess.call("FastCli -p15 -c 'show hsc detail ovsdb | cat > /mnt/flash/support/9.hsc-detail-ovsdb-$HOSTNAME.log'", shell=True)
        subprocess.call('echo ==[6/7]== cp /mnt/flash/openvswitch/vtep.db', shell=True)
        subprocess.call("sudo cp /mnt/flash/openvswitch/vtep.db /mnt/flash/support/10.vtep-$HOSTNAME.db", shell=True)
        subprocess.call('echo ==[7/7]== cp /var/log/secure* /mnt/flash/support/varlog/', shell=True)
        subprocess.call('echo ========= mkdir /mnt/flash/support/varlog', shell=True)
        subprocess.call('sudo mkdir /mnt/flash/support/varlog', shell=True)
        subprocess.call("sudo cp /var/log/secure* /mnt/flash/support/varlog/", shell=True)

    subprocess.call('echo ==[tar]== tar zcvf /mnt/flash/arista-hostname.tar.gz', shell=True)
    subprocess.call('sudo tar zcvf /mnt/flash/GT_$HOSTNAME-$(date +%m%d.%H%M).tar.gz /mnt/flash/support', shell=True)
    subprocess.call('echo ========= rm -rf /mnt/flash/support', shell=True)
    subprocess.call('sudo rm -rf /mnt/flash/support', shell=True)

def flash_delete():
    nodeleteFile = ( " -not -type d"
                " -not -name '.log'"
                " -not -name '*.swi'"
                                " -not -name '*.swix'"
                " -not -name 'initial*'"
                " -not -name 'startup-config'"
                " -not -name 'zerotouch-config'"
                " -not -name 'boot-config'"
                " -not -name 'fullrecover'"
                " -not -name 'auto-config.py'"
                " -not -name 'min-*.py'")
    subprocess.call("find /mnt/flash/ -maxdepth 1  "+ nodeleteFile + " -delete", shell=True)

def create_serial():
    return_info = switch.runCmds( 1, ["show interfaces management 1"])["result"][0]["interfaces"]["Management1"]["burnedInAddress"].split(":")
    vEOS_Serial = "SERIALNUMBER=MIN"+return_info[0]+return_info[1]+return_info[2]+return_info[3]+"\n"
    vEOS_SYSTEMMACADDR = "SYSTEMMACADDR="+return_info[0]+return_info[1]+"."+return_info[2]+return_info[3]+"."+return_info[4]+"01\n"
    f = open("/mnt/flash/veos-config", "w")
    f.write(vEOS_Serial)
    f.write(vEOS_SYSTEMMACADDR)
    f.close()

#### 실행
try:
    ### peer ping
    if len(sys.argv) == 1:
        peer_ping("show ip interface","P")
#    elif sys.argv[1] in {"pp"}:
#        peer_ping("show ip interface", sys.argv[1])
    elif sys.argv[1] in {"p","P","pp" }:
        peer_ping("show ip interface", sys.argv[1])
    ### description
    elif sys.argv[1] in {"d","dd","dD","D","Dd","DD"}:
        lldp_description("show lldp neighbors detail", sys.argv[1])
    ### help
    elif sys.argv[1] == 'support':
        arista_support()
    elif sys.argv[1] == 'delete':
        flash_delete()
    elif sys.argv[1] == 'veos':
        create_serial()
    else:
        print "Option [support]: case open - infomation save"                                      # gt support : case open 용 파일 저장
        print "Option [delete] : flash files delete"                                                       # gt delete  : dir, swi, start,zero 등 제외하고 파일 삭제
        print "Option [veos]   : vEOS Serial-Num and system-mac-address change"    # gt veos    : veos 에 시리얼 및 시스템맥 생성
        print "Option [P]      : Ping Information /31/30 subnet, More detail "     # gt p       : P2P 구간 ping 
        print "Option [pp]     : Ping Information all ip subnet, More detail "     
        print "Option [p]      : Ping Information /31/30 subnet"                   # gt P       : P2P 구간 ping detail 
        print "Option [d|dd]   : Apply to interfaces with lower"                   # gt dd      : 소문자 descrtiption
        print "Option [D|DD]   : Apply to interfaces with upper"                   # gt DD      : 대문자 descrtiption
except:
    print "Please contact GlobalTelecom"
finally:
    sys.exit()