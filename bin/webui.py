# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, render_template, request, redirect, url_for, Response

import numpy as np
import threading
import time

params = None

# --- Phone camera frame buffer ---
_phone_frame = None
_phone_frame_lock = threading.Lock()
_phone_frame_time = 0

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)
 
# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.
@app.route('/')
# '/' URL is bound with hello_world() function.
def hello_world():
    return render_template('index.html', name="there", smooth=np.round(params.additional_smoothing,2))
    
@app.route('/smoothing', methods=["POST"])
def smoothing():
    if request.form["action"] in options.keys():
        newvalue = params.additional_smoothing + 0.1*options[request.form["action"]]
    else:
        newvalue = float(request.form["value"])
    newvalue = np.clip(newvalue,0,1)
    params.change_additional_smoothing(newvalue,paramid=1)
    return redirect(url_for("hello_world"))
    
options = {
"<<":-10,
"<":-1,
">":1,
">>":10}

@app.route('/roty', methods=["POST"])
def roty():
    cur = params.euler_rot_y
    change = options[request.form["action"]]
    params.rot_change_y(cur+change)
    return redirect(url_for("hello_world"))
    
@app.route('/rotx', methods=["POST"])
def rotx():
    cur = params.euler_rot_x
    change = options[request.form["action"]]
    params.rot_change_x(cur+change)
    return redirect(url_for("hello_world"))
    
@app.route('/rotz', methods=["POST"])
def rotz():
    cur = params.euler_rot_z
    change = options[request.form["action"]]
    params.rot_change_z(cur+change)
    return redirect(url_for("hello_world"))
    
@app.route('/scale', methods=["POST"])
def scale():
    cur = params.posescale
    change = options[request.form["action"]] /100
    params.change_scale(cur+change)
    return redirect(url_for("hello_world"))
    
@app.route('/autocalib', methods=["POST"])
def autocalib():
    params.gui.autocalibrate()
    return redirect(url_for("hello_world"))

# ============================================================
# Phone Camera routes
# ============================================================

@app.route('/phone_camera')
def phone_camera():
    """Serves the phone camera page - open this on your phone's browser."""
    return render_template('phone_camera.html')

@app.route('/phone_camera_frame', methods=["POST"])
def phone_camera_frame():
    """Receives a JPEG frame from the phone browser."""
    global _phone_frame, _phone_frame_time
    data = request.get_data()
    if data:
        with _phone_frame_lock:
            _phone_frame = data
            _phone_frame_time = time.time()
    return "OK", 200

@app.route('/phone_camera_feed')
def phone_camera_feed():
    """MJPEG stream that OpenCV can read as a camera source."""
    def generate():
        last_sent = 0
        while True:
            with _phone_frame_lock:
                frame = _phone_frame
                frame_time = _phone_frame_time
            
            if frame is not None and frame_time > last_sent:
                last_sent = frame_time
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.01)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# main driver function
def start_webui(param, use_https=False):
    global params
    params=param
    # run() method of Flask class runs the application
    # on the local development server.
    print("INFO: Starting WebUI!")
    print("INFO: To access the webui, simply open the second Running on IP address on your quests browser!")
    print("INFO: ================================================")
    print("INFO: PHONE CAMERA: To use your phone as a camera,")
    print("INFO:   open https://<your-pc-ip>:5000/phone_camera on your phone's Safari/Chrome")
    print("INFO:   then set Camera ID to: http://127.0.0.1:5000/phone_camera_feed")
    print("INFO: ================================================")
    
    if use_https:
        try:
            app.run(host="0.0.0.0", ssl_context='adhoc')
        except Exception as e:
            print(f"WARN: Could not start HTTPS server ({e}), falling back to HTTP.")
            print("WARN: Phone camera may not work on iPhone Safari over HTTP.")
            print("WARN: Install pyopenssl: pip install pyopenssl")
            app.run(host="0.0.0.0")
    else:
        app.run(host="0.0.0.0")
