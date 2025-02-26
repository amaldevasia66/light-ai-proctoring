from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import os
import cv2
from utils.detection import start_proctoring
from utils.report import generate_report
from datetime import datetime
import base64
from io import BytesIO
from utils.combined_detection import detect_cheating
from PIL import Image
from utils.face_recognition import match_face
import numpy as np

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Global list to store cheating instances
cheating_instances = []

# Route: Home Page
@app.route('/')
def home():
    print('homeee')
    return render_template('home.html')

# Route: Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/capture_face', methods=['POST'])
def capture_face():
    name = request.form['name']
    roll_number = request.form['roll_number']
    image_data = request.form['image']

    # Decode the Base64 image data
    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)

    # Save the image
    image = Image.open(BytesIO(image_bytes))
    image_path = f'static/faces/{roll_number}.jpg'
    image.save(image_path)

    # Save user details
    with open('static/faces/users.txt', 'a') as file:
        file.write(f'{roll_number},{name}\n')

    return f"Face captured successfully for {name} ({roll_number})! Redirecting to home..."

# Route: Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        image_data = request.form['image']

        # Decode the Base64 image data
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        frame = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        # Check if roll number exists
        face_path = f'static/faces/{roll_number}.jpg'
        if not os.path.exists(face_path):
            return jsonify({"success": False, "error": "Roll number not found. Please register first."})

        # Check if user credentials are valid
        with open('static/faces/users.txt', 'r') as file:
            users = file.readlines()
            user_found = False
            for user in users:
                registered_roll_number, registered_name = user.strip().split(',')
                if roll_number == registered_roll_number and name.lower() == registered_name.lower():
                    user_found = True
                    break

            if not user_found:
                return jsonify({"success": False, "error": "Invalid name or roll number."})

        # Match the face
        if not match_face(roll_number, frame):
            return jsonify({"success": False, "error": "Face does not match the registered face."})

        # Successful login
        print(f"Login successful for roll number {roll_number}.")
        session['user'] = roll_number
        return jsonify({"success": True})

    return render_template('login.html')



@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        answers = {
            'q1': request.form['q1'],
            'q2': request.form['q2'],
            'q3': request.form['q3']
        }

        roll_number = session['user']
        student_name = ''
        with open('static/faces/users.txt', 'r') as file:
            for user in file.readlines():
                registered_roll_number, registered_name = user.strip().split(',')
                if roll_number == registered_roll_number:
                    student_name = registered_name
                    break
        print(f"Cheating instances: {cheating_instances}")
        # Generate report with cheating instances
        report_filename = f"static/reports/{roll_number}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generate_report(report_filename, student_name, roll_number, answers, cheating_instances)

        # Clear cheating instances after generating the report
        cheating_instances.clear()

        return redirect(url_for('home'))

    return render_template('exam.html')

@app.route('/video_feed')
def video_feed():
    print("Video feed route accessed")
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():

    global cheating_instances
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        print("Captured frame")
        # Detect cheating
        print("Calling detect_cheating function...")
        gaze_cheating, lip_cheating = detect_cheating(frame)
        print(f"Results - Gaze: {gaze_cheating}, Lip: {lip_cheating}")
        # Log cheating instances
        if gaze_cheating:
            cheating_instances.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "type": "Gaze Movement"
            })

        if lip_cheating:
            cheating_instances.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "type": "Lip Movement"
            })

        # Encode and stream the frame
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()


@app.route('/check_cheating')
def check_cheating():
    return jsonify({'cheating_detected': len(cheating_instances) > 0})

if __name__ == '__main__':
    if not os.path.exists('static/faces'):
        os.makedirs('static/faces')
    if not os.path.exists('static/temp'):
        os.makedirs('static/temp')
    if not os.path.exists('static/reports'):
        os.makedirs('static/reports')
    app.run(debug=True)