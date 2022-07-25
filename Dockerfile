# Dockerfile
FROM ubuntu:22.04 AS build-image
RUN apt update
RUN apt install software-properties-common
RUN apt-add-repository ppa:ansible/ansible
# 아파치 설치
RUN apt install apache2 python3.10 wget curl net-tools ansible -y
# RUN pip install ztpserver


FROM build-image 
# 아래의 설정으로 타임존 설정을 유예하는 것이기 때문에 차후에 따로 설정을 해주어야 합니다.
ENV DEBIAN_FRONTEND=noninteractive 

# RUN pip install mod_wsgi
# RUN mod_wsgi-express install-module
ADD excelToAvd.tar.gz /workspace/excelToAvd/


# RUN python /source/ztpserver/setup.py build
# RUN python /source/ztpserver/setup.py install
# 이미지에 소스 코드 카피


COPY requirements.txt /source/requirements.txt
RUN pip install -r /source/requirements.txt
 
# # 카피한 가상 호스트 설정 파일 심볼 링크 설정
RUN ln -s /etc/apache2/sites-available/ztpserver.conf /etc/apache2/sites-enabled/


 
EXPOSE 8080


## requests 2.27.1
## pip install PyYAML==5.3.1
# CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]


## isc-dhcp-server

# vi /etc/dhcp/dhcpd.conf

# subnet 172.17.0.0 netmask 255.255.255.0 {
#   range 172.17.0.5 172.17.0.204;
#   option routers 172.17.0.1;

#   # Only return the bootfile-name to Arista devices
#   class "Arista" {
#     match if substring(option vendor-class-identifier, 0, 6) = "Arista";
#     option bootfile-name "http://0.0.0.0:8080/bootstrap";
#   }
# }


# vi /etc/default/isc-dhcp-server

#INTERFACESv4=""
#INTERFACESv6=""
#INTERFACES="eth0"

# /etc/init.d/isc-dhcp-server restart