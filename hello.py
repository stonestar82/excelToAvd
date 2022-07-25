# hello.py
from flask import Flask, request
import subprocess
import shlex
import urllib.parse

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/meet")
def meet():
    return "Nice to meet you!"


@app.route("/save",methods = ['POST', 'GET'])
def save():
    
    print("============")
    command = "python main.py"
    print(command)
    print('Started executing command')
    command = shlex.split(command)
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    print("Run successfully")
    output, err = process.communicate()
    return output


@app.route("/design",methods = ['POST', 'GET'])
def design():
    
    print("============")
    command = "ansible-playbook design.yml"
    print(command)
    print('Started executing command')
    command = shlex.split(command)
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    print("Run successfully")
    output, err = process.communicate()
    return output

@app.route("/config",methods = ['POST', 'GET'])
def config():
    
    print("============")
    command = "ansible-playbook config.yml"
    print(command)
    print('Started executing command')
    command = shlex.split(command)
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    print("Run successfully")
    output, err = process.communicate()
    return output

@app.route("/deploy",methods = ['POST', 'GET'])
def deploy():
    
    print("============")
    command = "ansible-playbook deploy.yml"
    print(command)
    print('Started executing command')
    command = shlex.split(command)
    process = subprocess.Popen(command, stdout = subprocess.PIPE)
    print("Run successfully")
    output, err = process.communicate()
    return output


if __name__ == '__main__':
    app.run(host='0.0.0.0')
