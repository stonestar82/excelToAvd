from flask import Flask, render_template, request, Response
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="static/templates")

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def index():

  switchList = os.listdir("./inventory/intended/configs/", )
  
  return render_template('switchList.html', switchList=switchList)

@app.route("/switch/<switch>")
def read(switch): 

  try:
    with open('./inventory/intended/configs/' + secure_filename(switch) + '.cfg', encoding="UTF-8") as f:
      cfg = f.readlines()
  except FileNotFoundError:
      cfg = ["설정파일이 없습니다."]

  return render_template('cfg.html', cfg=cfg)

@app.route("/cfgs/<switch>")
def cfgs(switch):
  try:
    with open('./inventory/intended/configs/' + secure_filename(switch) + '.cfg', encoding="UTF-8") as f:
      cfg = f.readlines()
      return "\n".join(cfg)
  except FileNotFoundError:
      return Response("", status=404, mimetype='application/json')

  

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
  
@app.route("/bootstrap")
def bootstrap():

  with open('./bootstrap.py', encoding="UTF-8") as f:
    boot = f.readlines()
    return "\n".join(boot)
    
  return ""