from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np

from image_cnn_detector import ImageCNNDetector
from database import Database

# =========================
# APP SETUP
# =========================
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)

CORS(app, supports_credentials=True)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB for videos
app.config['SECRET_KEY'] = 'change-this-in-production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# =========================
# INITIALIZE COMPONENTS
# =========================
image_detector = ImageCNNDetector("ai_image_model.h5")
db = Database()

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif',
    'mp4', 'avi', 'mov'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =========================
# VIDEO ANALYSIS FUNCTION
# =========================
def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)

    frame_predictions = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Analyze every 10th frame
        if frame_count % 10 == 0:
            frame = cv2.resize(frame, (224, 224))
            frame = frame / 255.0
            frame = np.expand_dims(frame, axis=0)

            prediction = image_detector.model.predict(frame)[0][0]
            frame_predictions.append(prediction)

        frame_count += 1

    cap.release()

    if not frame_predictions:
        return {"error": "No frames extracted from video"}

    avg_prediction = np.mean(frame_predictions)

    # fake = 0, real = 1
    is_ai = avg_prediction < 0.5
    confidence = float((1 - avg_prediction) * 100 if is_ai else avg_prediction * 100)

    return {
        "isAI": bool(is_ai),
        "confidence": round(confidence, 2),
        "verdict": "AI Generated" if is_ai else "Real/Human Created",
        "details": "Video frame-based CNN analysis",
        "indicators": []
    }


# =========================
# ROOT
# =========================
@app.route('/')
def home():
    return render_template('index.html')


# =========================
# HEALTH CHECK
# =========================
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


# =========================
# AUTH
# =========================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = db.verify_user(data.get('email'), data.get('password'))

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user['id']
    return jsonify({'user': user})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    user = db.create_user(data['name'], data['email'], data['password'])

    if not user:
        return jsonify({'error': 'Email already exists'}), 400

    session['user_id'] = user['id']
    return jsonify({'user': user})


# =========================
# ANALYZE (IMAGE + VIDEO)
# =========================
@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    try:
        extension = filename.rsplit('.', 1)[1].lower()

        # IMAGE
        if extension in ['png', 'jpg', 'jpeg', 'gif']:
            result = image_detector.predict(path)

        # VIDEO
        elif extension in ['mp4', 'avi', 'mov']:
            result = analyze_video(path)

        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Add metadata
        result['fileName'] = filename
        result['fileSize'] = f"{os.path.getsize(path) / 1024:.2f} KB"
        result['fileType'] = file.content_type

        # Save to DB
        user_id = session.get('user_id', 1)
        db.save_analysis(
            user_id,
            filename,
            result['fileSize'],
            result['fileType'],
            int(result['isAI']) if result.get('isAI') is not None else None,
            float(result['confidence']),
            result['verdict']
        )

        os.remove(path)

        return jsonify(result)

    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        return jsonify({'error': str(e)}), 500


# =========================
# HISTORY
# =========================
@app.route('/api/history')
def history():
    user_id = session.get('user_id', 1)
    return jsonify({'history': db.get_user_history(user_id)})


# =========================
# RUN SERVER
# =========================
if __name__ == '__main__':
    print("🚀 Backend running at http://localhost:5000")
    app.run(debug=True)
