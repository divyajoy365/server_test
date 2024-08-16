from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import base64
import numpy as np
from gevent import monkey
import gevent
import random
from geventwebsocket.handler import WebSocketHandler

# Patch sockets to make them compatible with gevent
# will the one process vs application be 
monkey.patch_all()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True)

# Video capture object
video_capture = cv2.VideoCapture(0)  # 0 is the default webcam

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to the server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def generate_frames():
    while True:
        success, frame = video_capture.read()  # Read frame from webcam
        if not success:
            break
        else:
            # Convert frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Encode the JPEG image to base64
            # websockets uses JSON for data transmission which is able to send text but not binary data hence the encoding
            # represents image as a string
            frame_base64 = base64.b64encode(frame).decode('utf-8') 

            yield frame_base64 # different to return. Along with the While True, this keeps returning the next frame 
            #i.e. it is like a conveyer belt
            # if it was a return, it would terminate the whole function - which we don't want



# When the client calls for 'request_frame', this function is triggered
@socketio.on('request_frame')
def handle_request_frame():
    for frame_base64 in generate_frames():
        emit('new_frame', {'frame': frame_base64})
        gevent.sleep(0.1)  # Adjust the frame rate as needed


# This sends the new sensor data to the client via sockets
# the while TRUE sets an infinite for loop that keeps sending the data 
def simulate_sensor_readings():
    while True:
        # Simulate sensor data
        sensor_data = {
            'temperature': round(random.uniform(20.0, 30.0), 2),  # Temperature 
            'humidity': round(random.uniform(30.0, 60.0), 2),      # Humidity 
        }
        # Emit sensor data to the client
        socketio.emit('sensor_update', sensor_data)
        gevent.sleep(2)  # Wait for 2 seconds

# Start the sensor simulation in a green thread
# this calls the above function
gevent.spawn(simulate_sensor_readings)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, log_output=True)
