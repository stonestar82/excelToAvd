from flask import Flask, Blueprint, render_template, request
import os
from werkzeug.utils import secure_filename


app = Flask(__name__, template_folder="static/templates")

@app.route("/")
def index():

  # POST (JSON)
  # url = "http://123.215.15.157/api/auth/login"
  # headers = {'Content-Type': 'application/json; chearset=utf-8'}
  # data = {'username': 'pks', 'password': 'rkqtn!23'}
  # res = requests.post(url, data=json.dumps(data), headers=headers)

  # loginResponse = res.json()
  
  # return render_template('index.html', loginState=loginResponse)

  switchList = os.listdir("./inventory/intended/configs/", )
  
  return render_template('switchList.html', switchList=switchList)


@app.route("/read/<switch>")
def read(switch): 

  try:
    with open('./inventory/intended/configs/' + switch + '.cfg') as f:
      cfg = f.readlines()
  except FileNotFoundError:
      cfg = ["설정파일이 없습니다."]

  return render_template('cfg.html', cfg=cfg)


@app.route("/cfg/input")
def configInput(): 


  return render_template('configInput.html')

@app.route("/cfg/upload", methods = ['POST'])
def configUpload(): 

  f = request.files["cfg_file"]
  f.save(secure_filename(f.filename))

  return "파일이 저장되었습니다."
    
# app.run(port=80) 