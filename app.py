from flask import Flask, send_from_directory, render_template, request, blueprints
import os
from werkzeug.utils import secure_filename


app = Flask(__name__, template_folder="static/templates")

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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


@app.route("/switch/<switch>")
def switch(switch): 

  try:
    with open('./inventory/intended/configs/' + switch + '.cfg', encoding="UTF-8") as f:
      cfg = f.readlines()
  except FileNotFoundError:
      cfg = ["설정파일이 없습니다."]

  return render_template('cfg.html', cfg=cfg)


@app.route("/cfgs/<switch>")
def cfg(switch): 
  return send_from_directory(directory='./inventory/intended/configs/', filename=secure_filename(switch))


@app.route("/cfg/input")
def configInput():
  return render_template('configInput.html')

@app.route("/cfg/upload", methods = ['POST'])
def configUpload(): 

  f = request.files["cfg_file"]
  f.save("/avd/upload/" + secure_filename(f.filename))

  return "파일이 저장되었습니다."

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=80) 