from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from PIL import Image
import base64
from io import BytesIO
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import cv2
from datetime import datetime
import uuid
from bson.objectid import ObjectId
import json
from guidance import WasteGuidance, guidance_bp, waste_guidance
from constants import WASTE_EDUCATION
import bcrypt
import re


app = Flask(__name__)
app.register_blueprint(guidance_bp)
load_dotenv()

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# MongoDB Setup
client = MongoClient(os.getenv('MONGO_URI'))
db = client['greenguide']
users = db['users']
reports = db['reports']
educational_content = db['educational_content']



# Load models
try:
    waste_classification_model = tf.keras.models.load_model('GGG/models/best_model.h5')
    surveillance_model = tf.keras.models.load_model('GGG/models/Street_model.h5')
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}. Please ensure models are in the 'models' directory.")
    waste_classification_model = None
    surveillance_model = None

waste_guidance = WasteGuidance()

def preprocess_classification_image(image):
    img = image.resize((224, 224))
    img_array = img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def classify_waste(image):
    if waste_classification_model is None:
        return {"error": "Model not loaded"}
    
    img_array = preprocess_classification_image(image)
    predictions = waste_classification_model.predict(img_array)
    classes = waste_guidance.waste_types
    predicted_class = classes[np.argmax(predictions)]
    confidence = float(np.max(predictions))
    
    top_indices = np.argsort(predictions[0])[-3:][::-1]
    alternatives = [
        {'waste_type': classes[idx], 'confidence': float(predictions[0][idx])}
        for idx in top_indices[1:] if predictions[0][idx] > 0.05
    ]
    
    return {
        'waste_type': predicted_class,
        'confidence': confidence,
        'guidance': waste_guidance.get_guidance_for_waste_type(predicted_class),
        'alternatives': alternatives,
        'guidance_url': url_for('guidance.waste_guidance_view', waste_type=predicted_class)
    }
# Email validation function
def is_valid_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        # Validate email format
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('login.html')

        # Find user in MongoDB
        user = users.find_one({'email': email})
        if user and bcrypt.checkpw(password, user['password']):
            session['logged_in'] = True  # Set logged_in flag
            session['email'] = email    # Consistent key
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))  # Redirect to profile instead of index
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))  # Redirect to index

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        # Validate email format
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('register.html')

        # Check if email already exists
        if users.find_one({'email': email}):
            flash('Email already exists', 'error')
        else:
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            users.insert_one({'email': email, 'password': hashed})
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Profile route
@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_email = session.get('email')  # Consistent with login
    user = users.find_one({'email': user_email})  # Correct MongoDB query
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=user)

@app.route('/classify', methods=['GET', 'POST'])
def classify():
    if request.method == 'POST':
        if 'image' in request.form:
            image_data = request.form['image']
            image = Image.open(BytesIO(base64.b64decode(image_data.split(',')[1])))
        elif 'file' in request.files:
            file = request.files['file']
            image = Image.open(file)
        else:
            return render_template('classify.html', error='No image provided'), 400
        
        result = classify_waste(image)
        return render_template('classification_results.html', result=result)
    
    return render_template('classify.html')

@app.route('/education')
def education():
    """Educational resources about waste management"""
    # Add guidance URLs to waste categories using waste_guidance
    waste_types_with_guidance = {}
    for waste_type in waste_guidance.waste_types:
        guidance = waste_guidance.get_guidance_for_waste_type(waste_type)
        waste_types_with_guidance[waste_type] = guidance or {}
        waste_types_with_guidance[waste_type]['guidance_url'] = url_for('guidance.waste_guidance_view', waste_type=waste_type)
    
    return render_template('education.html', 
                           waste_types=waste_types_with_guidance, 
                           education=WASTE_EDUCATION)

@app.route('/report')
def report():
    return "Report page under construction"

@app.route('/surveillance')
def surveillance():
    return "Survillance page under construction"


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('404.html'), 500  ## we can change it

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)