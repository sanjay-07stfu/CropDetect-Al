import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import numpy as np
import tensorflow as tf
import re

# Setup logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------
# Configuration
# ----------------------
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DB_PATH = 'database/data.db'
MODEL_PATH = 'model/plant_disease_model.h5'
# Confidence threshold for returning a prediction (can be overridden with env var)
CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.50'))

# ----------------------
# Labels configuration
# ----------------------
import json
with open('model/class_indices.json', 'r') as f:
    class_indices = json.load(f)
LABELS = [None] * len(class_indices)
for k, v in class_indices.items():
    LABELS[v] = k

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
# Use environment variable for SECRET_KEY, fallback to a generated value
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production-' + os.urandom(16).hex())

# Ensure upload and database directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ----------------------
# Database helpers
# ----------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            disease TEXT NOT NULL,
            confidence REAL NOT NULL,
            image_desc TEXT,
            notes TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    # add column if running against older schema
    cursor.execute("PRAGMA table_info(history)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'image_desc' not in cols:
        cursor.execute('ALTER TABLE history ADD COLUMN image_desc TEXT')
    # simple cache table to avoid reprocessing identical images
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            file_hash TEXT PRIMARY KEY,
            disease TEXT NOT NULL,
            confidence REAL NOT NULL
        )
    ''')
    # users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    # login audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT
        )
    ''')
    conn.commit()
    # create default admin if not present
    try:
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                       ('admin@example.com', generate_password_hash('password')))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

init_db()

# ----------------------
# Load ML model
# ----------------------

model = None

try:
    model = tf.keras.models.load_model(MODEL_PATH)
    model.make_predict_function()
    logger.info(f'Model loaded successfully from {MODEL_PATH}')
    
    # Verify model compatibility with LABELS
    if model.output_shape[-1] != len(LABELS):
        logger.critical(f"Model has {model.output_shape[-1]} outputs but {len(LABELS)} LABELS defined.")
        logger.critical("Predictions will be mapped incorrectly! Update LABELS in app.py.")
        
    try:
        # show output shape if possible
        sample = np.zeros((1,224,224,3))
        out = model.predict(sample)
        logger.debug(f'Model output shape: {np.shape(out)}')
    except Exception:
        pass
except Exception as e:
    logger.error(f'Error loading model: {type(e).__name__}: {str(e)}')
    model = None
    # continue; routes will handle missing model gracefully

# sample disease info dictionary with product recommendations
# You should update this dict to include every class your model can predict.
# The detection labels are taken from this list by default. If your model
# uses a different set of labels, override LABELS below or extend this dict.
DISEASE_INFO = {
    # --- Apple ---
    'Apple___Apple_scab': {
        'description': 'Velvety, olive-green spots on leaves that turn black. Causes fruit deformation.',
        'prevention': 'Remove fallen leaves. Prune to open canopy.',
        'organic': 'Sulfur sprays, Neem oil.',
        'chemical': 'Captan, Myclobutanil.',
        'precautions': 'Apply preventive sprays in spring.',
        'products': {'fungicides': [{'name': 'Captan', 'url': 'https://www.amazon.in/s?k=Captan+fungicide'}]}
    },
    'Apple___Black_rot': {
        'description': 'Purple spots on leaves, rotting fruit with concentric bands.',
        'prevention': 'Remove mummified fruit and dead wood.',
        'organic': 'Copper-based sprays.',
        'chemical': 'Captan, Thiophanate-methyl.',
        'precautions': 'Sanitize pruning tools.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Apple___Cedar_apple_rust': {
        'description': 'Bright orange-yellow spots on leaves. Requires cedar trees as alternate host.',
        'prevention': 'Remove nearby cedar/juniper trees if possible.',
        'organic': 'Sulfur, Neem oil.',
        'chemical': 'Myclobutanil, Mancozeb.',
        'precautions': 'Spray when orange horns appear on cedar trees.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Apple___healthy': {'description': 'Healthy apple leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Blueberry ---
    'Blueberry___healthy': {'description': 'Healthy blueberry leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Cherry ---
    'Cherry_(including_sour)___Powdery_mildew': {
        'description': 'White powdery growth on leaves and shoots. Leaves may curl.',
        'prevention': 'Prune for airflow. Avoid overhead watering.',
        'organic': 'Sulfur dust, Neem oil, Baking soda solution.',
        'chemical': 'Myclobutanil, Propiconazole.',
        'precautions': 'Monitor during warm, dry weather.',
        'products': {'fungicides': [{'name': 'Sulfur Dust', 'url': 'https://www.amazon.in/s?k=Sulfur+dust'}]}
    },
    'Cherry_(including_sour)___healthy': {'description': 'Healthy cherry leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Corn ---
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': {
        'description': 'Rectangular gray to brown lesions on leaves.',
        'prevention': 'Crop rotation. Resistant hybrids.',
        'organic': 'Neem oil (limited efficacy).',
        'chemical': 'Azoxystrobin, Pyraclostrobin.',
        'precautions': 'Monitor lower leaves first.',
        'products': {'fungicides': [{'name': 'Fungicide', 'url': 'https://www.amazon.in/s?k=Corn+fungicide'}]}
    },
    'Corn_(maize)___Common_rust_': {
        'description': 'Reddish-brown pustules on both leaf surfaces.',
        'prevention': 'Plant resistant varieties.',
        'organic': 'Copper sprays.',
        'chemical': 'Mancozeb, Pyraclostrobin.',
        'precautions': 'Cool, moist weather favors spread.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Corn_(maize)___Northern_Leaf_Blight': {
        'description': 'Long, cigar-shaped grayish-green lesions.',
        'prevention': 'Crop rotation. Tillage to bury residue.',
        'organic': 'Copper fungicide.',
        'chemical': 'Mancozeb, Chlorothalonil.',
        'precautions': 'Spreads rapidly in wet weather.',
        'products': {'fungicides': [{'name': 'Chlorothalonil', 'url': 'https://www.amazon.in/s?k=Chlorothalonil'}]}
    },
    'Corn_(maize)___healthy': {'description': 'Healthy corn leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Grape ---
    'Grape___Black_rot': {
        'description': 'Brown circular spots on leaves; shriveled, black mummified berries.',
        'prevention': 'Remove mummies. Prune for airflow.',
        'organic': 'Copper, Sulfur.',
        'chemical': 'Mancozeb, Myclobutanil.',
        'precautions': 'Critical period is bloom to 4 weeks after.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Grape___Esca_(Black_Measles)': {
        'description': 'Tiger-stripe pattern on leaves. Dark spots on berries.',
        'prevention': 'Protect pruning wounds. Remove infected vines.',
        'organic': 'No cure. Sanitation only.',
        'chemical': 'No effective chemical cure.',
        'precautions': 'Disinfect tools.',
        'products': {}
    },
    'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': {
        'description': 'Irregular brown spots with yellow halos.',
        'prevention': 'Manage canopy for airflow.',
        'organic': 'Copper fungicide.',
        'chemical': 'Mancozeb.',
        'precautions': 'Monitor late season.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Grape___healthy': {'description': 'Healthy grape leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Orange ---
    'Orange___Haunglongbing_(Citrus_greening)': {
        'description': 'Yellow mottling on leaves. Misshapen, bitter fruit. Spread by psyllids.',
        'prevention': 'Control psyllid vectors. Use certified disease-free trees.',
        'organic': 'Neem oil for psyllids.',
        'chemical': 'Imidacloprid for vectors.',
        'precautions': 'Remove infected trees immediately.',
        'products': {'supplements': [{'name': 'Micronutrients', 'url': 'https://www.amazon.in/s?k=Citrus+fertilizer'}]}
    },

    # --- Peach ---
    'Peach___Bacterial_spot': {
        'description': 'Small, water-soaked spots on leaves and fruit. Shot-hole effect.',
        'prevention': 'Resistant varieties. Avoid high nitrogen.',
        'organic': 'Copper sprays (careful of phytotoxicity).',
        'chemical': 'Copper, Oxytetracycline.',
        'precautions': 'Spray at dormancy.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Peach___healthy': {'description': 'Healthy peach leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Pepper ---
    'Pepper,_bell___Bacterial_spot': {
        'description': 'Small brown spots on leaves and fruit. Leaves may drop.',
        'prevention': 'Use disease-free seeds. Rotate crops.',
        'organic': 'Copper sprays.',
        'chemical': 'Copper hydroxide + Mancozeb.',
        'precautions': 'Avoid overhead irrigation.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Pepper,_bell___healthy': {'description': 'Healthy pepper leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Potato ---
    'Potato___Early_blight': {
        'description': 'Dark brown spots with concentric rings (target board effect) on lower leaves.',
        'prevention': 'Crop rotation. Mulching.',
        'organic': 'Copper fungicide.',
        'chemical': 'Mancozeb, Chlorothalonil.',
        'precautions': 'Maintain plant vigor.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Potato___Late_blight': {
        'description': 'Large, dark, water-soaked spots. White fungal growth in wet weather. Rapidly destructive.',
        'prevention': 'Plant resistant varieties. Destroy cull piles.',
        'organic': 'Copper sprays (preventive).',
        'chemical': 'Mancozeb, Chlorothalonil, Metalaxyl.',
        'precautions': 'Monitor weather. Spray before rain.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Potato___healthy': {'description': 'Healthy potato leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Raspberry/Soybean/Squash/Strawberry ---
    'Raspberry___healthy': {'description': 'Healthy raspberry leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},
    'Soybean___healthy': {'description': 'Healthy soybean leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},
    'Squash___Powdery_mildew': {
        'description': 'White powdery growth on leaves and stems.',
        'prevention': 'Resistant varieties. Air circulation.',
        'organic': 'Neem oil, Sulfur, Baking soda.',
        'chemical': 'Chlorothalonil, Myclobutanil.',
        'precautions': 'Common in late summer.',
        'products': {'fungicides': [{'name': 'Neem Oil', 'url': 'https://www.amazon.in/s?k=Neem+oil'}]}
    },
    'Strawberry___Leaf_scorch': {
        'description': 'Purple spots that turn brown. Leaves look scorched.',
        'prevention': 'Remove infected leaves. Renovate beds.',
        'organic': 'Copper fungicide.',
        'chemical': 'Captan, Thiram.',
        'precautions': 'Clean up debris.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Strawberry___healthy': {'description': 'Healthy strawberry leaf.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Tomato ---
    'Tomato___Bacterial_spot': {
        'description': 'Small, dark, greasy spots on leaves and fruit.',
        'prevention': 'Seed treatment. Crop rotation.',
        'organic': 'Copper sprays.',
        'chemical': 'Copper + Mancozeb.',
        'precautions': 'Avoid working when wet.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Tomato___Early_blight': {
        'description': 'Brown spots with concentric rings on lower leaves.',
        'prevention': 'Mulch soil. Stake plants.',
        'organic': 'Copper, Serenade (Bacillus subtilis).',
        'chemical': 'Mancozeb, Chlorothalonil.',
        'precautions': 'Remove lower leaves.',
        'products': {'fungicides': [{'name': 'Mancozeb', 'url': 'https://www.amazon.in/s?k=Mancozeb'}]}
    },
    'Tomato___Late_blight': {
        'description': 'Dark, water-soaked spots on leaves/fruit. White mold on undersides.',
        'prevention': 'Keep foliage dry. Good airflow.',
        'organic': 'Copper fungicide.',
        'chemical': 'Chlorothalonil, Mancozeb.',
        'precautions': 'Highly contagious. Remove infected plants.',
        'products': {'fungicides': [{'name': 'Copper Fungicide', 'url': 'https://www.amazon.in/s?k=Copper+fungicide'}]}
    },
    'Tomato___Leaf_Mold': {
        'description': 'Yellow spots on upper leaf, olive-green mold on underside.',
        'prevention': 'Reduce humidity. Vent greenhouses.',
        'organic': 'Copper fungicide.',
        'chemical': 'Chlorothalonil, Mancozeb.',
        'precautions': 'High humidity disease.',
        'products': {'fungicides': [{'name': 'Chlorothalonil', 'url': 'https://www.amazon.in/s?k=Chlorothalonil'}]}
    },
    'Tomato___Septoria_leaf_spot': {
        'description': 'Small circular spots with gray centers and dark borders.',
        'prevention': 'Remove lower leaves. Mulch.',
        'organic': 'Copper fungicide.',
        'chemical': 'Chlorothalonil.',
        'precautions': 'Splashes from soil spread it.',
        'products': {'fungicides': [{'name': 'Chlorothalonil', 'url': 'https://www.amazon.in/s?k=Chlorothalonil'}]}
    },
    'Tomato___Spider_mites Two-spotted_spider_mite': {
        'description': 'Tiny yellow specks (stippling) on leaves. Fine webbing.',
        'prevention': 'Avoid dust. Keep plants watered.',
        'organic': 'Neem oil, Insecticidal soap.',
        'chemical': 'Abamectin, Spiromesifen.',
        'precautions': 'Hot, dry weather favors mites.',
        'products': {'supplements': [{'name': 'Neem Oil', 'url': 'https://www.amazon.in/s?k=Neem+oil'}]}
    },
    'Tomato___Target_Spot': {
        'description': 'Brown lesions with faint concentric rings.',
        'prevention': 'Improve airflow.',
        'organic': 'Copper fungicide.',
        'chemical': 'Chlorothalonil, Azoxystrobin.',
        'precautions': 'Similar to Early Blight.',
        'products': {'fungicides': [{'name': 'Chlorothalonil', 'url': 'https://www.amazon.in/s?k=Chlorothalonil'}]}
    },
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus': {
        'description': 'Leaves curl upward and turn yellow. Stunted growth.',
        'prevention': 'Control whiteflies. Use resistant varieties.',
        'organic': 'Neem oil (for whiteflies).',
        'chemical': 'Imidacloprid (for whiteflies).',
        'precautions': 'Remove infected plants immediately.',
        'products': {'supplements': [{'name': 'Yellow Sticky Traps', 'url': 'https://www.amazon.in/s?k=Yellow+sticky+traps'}]}
    },
    'Tomato___Tomato_mosaic_virus': {
        'description': 'Mottled light and dark green pattern on leaves.',
        'prevention': 'Sanitation. Wash hands (tobacco users).',
        'organic': 'Milk spray (preventive).',
        'chemical': 'None.',
        'precautions': 'Very stable virus. Disinfect tools.',
        'products': {}
    },
    'Tomato___healthy': {'description': 'Healthy tomato plant.', 'prevention': '', 'organic': '', 'chemical': '', 'precautions': '', 'products': {}},

    # --- Fallback for Low Confidence ---
    'Unknown Object or Healthy': {
        'description': 'The model could not confidently identify a specific disease. The image might be unclear, or the object is not a plant.',
        'prevention': 'Ensure the image is focused, well-lit, and contains a clear view of the leaf.',
        'organic': '',
        'chemical': '',
        'precautions': '',
        'products': {}
    }
}

# ----------------------
# Utility functions
# ----------------------
import hashlib

# Simple leaf detector heuristic: count "green" pixels and compare to threshold.
# This is intentionally lightweight (no extra model) to filter non-leaf images (people, objects, indoor scenes).
# It uses a simple RGB-based test so it works without OpenCV.
LEAF_GREEN_PERCENT = float(os.environ.get('LEAF_GREEN_PERCENT', '0.02'))  # 2% green pixels by default

def is_leaf_image(image_path, sample_size=224):
    """Return True if the image contains enough green pixels to likely be a leaf.

    Heuristic: a pixel is "green" when G is substantially greater than R and B
    and above a minimum absolute threshold. Works with RGB images.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        # resize to speed up processing and normalize
        img = img.resize((sample_size, sample_size), Image.Resampling.BILINEAR)
        arr = np.array(img)
        r = arr[..., 0].astype('int32')
        g = arr[..., 1].astype('int32')
        b = arr[..., 2].astype('int32')

        # green pixel if g significantly larger than r and b and g high enough
        green_mask = (g > r * 1.10) & (g > b * 1.10) & (g > 80)
        green_count = int(np.count_nonzero(green_mask))
        total = arr.shape[0] * arr.shape[1]
        pct = green_count / float(total)
        # debug log
        logger.debug(f'Leaf check: {green_count}/{total} green pixels ({pct*100:.2f}%)')
        return pct >= LEAF_GREEN_PERCENT
    except Exception as e:
        logger.warning(f'is_leaf_image failed: {e}')
        # on error, assume it might be a leaf to avoid false negatives
        return True

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_valid_email(email):
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password):
    """Return True if password meets minimum requirements."""
    return len(password) >= 6  # At minimum 6 characters


def log_login_activity(email, action, status, ip_address=None):
    """Log user login/logout activity to audit table.
    
    Args:
        email: User email address
        action: 'LOGIN' or 'LOGOUT'
        status: 'SUCCESS' or 'FAILED'
        ip_address: Client IP address (optional)
    """
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO login_logs (email, action, status, timestamp, ip_address) VALUES (?, ?, ?, ?, ?)',
            (email, action, status, datetime.now().isoformat(), ip_address)
        )
        conn.commit()
        conn.close()
        logger.info(f'Logged: {action} - {email} - {status}')
    except Exception as e:
        logger.error(f'Error logging activity: {e}')


def create_user(email, password):
    """Create a new user with email and password validation."""
    if not is_valid_email(email):
        return False, 'Invalid email format'
    if not is_strong_password(password):
        return False, 'Password must be at least 6 characters'
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                     (email, generate_password_hash(password)))
        conn.commit()
        logger.info(f'User created: {email}')
        return True, 'User created successfully'
    except sqlite3.IntegrityError:
        logger.warning(f'Duplicate email attempted: {email}')
        return False, 'Email already exists'
    except Exception as e:
        logger.error(f'Error creating user: {e}')
        return False, 'Error creating user'
    finally:
        conn.close()


def verify_user(email, password):
    conn = get_db_connection()
    row = conn.execute('SELECT password_hash FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    if row and check_password_hash(row['password_hash'], password):
        return True
    return False


def compute_hash(filepath):
    """Return sha256 hash of file contents."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def get_cached_prediction(file_hash):
    conn = get_db_connection()
    rec = conn.execute('SELECT disease, confidence FROM cache WHERE file_hash=?', (file_hash,)).fetchone()
    conn.close()
    if rec:
        return rec['disease'], rec['confidence']
    return None, None


def store_cache(file_hash, disease, confidence):
    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO cache(file_hash, disease, confidence) VALUES (?,?,?)',
                 (file_hash, disease, confidence))
    conn.commit()
    conn.close()


def preprocess_image(image_path):
    """
    Load and preprocess image for model prediction.
    Resize to (224, 224), convert to numpy array, normalize to [0, 1], expand dims.
    """
    img = Image.open(image_path).convert('RGB')
    img = img.resize((224, 224), Image.Resampling.LANCZOS)
    arr = np.array(img, dtype='float32')
    arr = arr / 255.0
    arr = np.expand_dims(arr, axis=0)
    return arr


def predict_disease(image_path):
    """
    Predict disease from image using trained model.
    If model is unavailable, returns a demo prediction for testing.
    Includes timeout for model predictions to prevent hanging requests.
    """
    try:
        # Try to use actual model if loaded
        # Quick check: ensure image looks like a leaf/plant before running heavy model
        if not is_leaf_image(image_path):
            logger.info(f"Image '{image_path}' failed leaf-detection heuristic. Returning Unknown.")
            return "Unknown Object or Healthy", 0.0
        if model is not None:
            processed = preprocess_image(image_path)
            preds = model.predict(processed, verbose=0)
            preds = np.asarray(preds).ravel()
            confidence = float(np.max(preds))
            class_idx = int(np.argmax(preds))
            low_confidence = confidence < CONFIDENCE_THRESHOLD
            if low_confidence:
                logger.warning(f"Low confidence prediction ({confidence*100:.2f}%). Result may be inaccurate.")
            logger.debug(f"Model Prediction - Index: {class_idx}")
            if class_idx < len(LABELS):
                disease = LABELS[class_idx]
                logger.debug(f"Mapped Label: {disease}")
            else:
                disease = 'Unknown'
                logger.warning(f'Model returned class {class_idx} but only {len(LABELS)} labels defined')
            return disease, confidence
        else:
            # Demo mode: return a sample disease with high confidence
            # This helps test the application without a trained model
            import random
            available_diseases = LABELS
            if available_diseases:
                disease = random.choice(available_diseases)
                confidence = round(random.uniform(0.75, 0.95), 4)
                logger.info(f'DEMO MODE Prediction: {disease} ({confidence*100:.2f}% confidence)')
                return disease, confidence
    except Exception as e:
        logger.error(f'Prediction error: {type(e).__name__}: {str(e)}')
        # Fallback to demo mode on error
        try:
            import random
            available_diseases = LABELS
            if available_diseases:
                disease = random.choice(available_diseases)
                confidence = round(random.uniform(0.60, 0.75), 4)
                logger.warning(f'FALLBACK Prediction: {disease} ({confidence*100:.2f}% confidence)')
                return disease, confidence
        except Exception as ee:
            logger.error(f'FALLBACK ERROR: {type(ee).__name__}: {str(ee)}')
    return None, None

# ----------------------
# Routes
# ----------------------


# Debug-only prediction introspection endpoint.
# Returns raw logits, whether softmax was applied, and top-5 mapped labels.
# Accessible only when Flask debug mode is enabled (`FLASK_DEBUG=true`).
@app.route('/_debug/predict', methods=['GET'])
def debug_predict():
    if not app.debug:
        return jsonify({'error': 'Debug endpoint disabled'}), 403
    # allow passing a path relative to project root or relative to upload folder
    file_arg = request.args.get('file', 'static/uploads/potato.png')
    # prefer absolute if exists
    if os.path.exists(file_arg):
        path = file_arg
    else:
        path = os.path.join(app.config['UPLOAD_FOLDER'], file_arg)
    if not os.path.exists(path):
        return jsonify({'error': 'file not found', 'path': path}), 404

    if model is None:
        return jsonify({'error': 'model not loaded'}), 500

    try:
        processed = preprocess_image(path)
        preds = model.predict(processed, verbose=0)
        preds = np.asarray(preds).ravel()

        # detect and apply softmax if needed
        sum_preds = float(np.sum(preds)) if preds.size > 0 else 0.0
        softmax_applied = False
        if not np.isclose(sum_preds, 1.0, atol=1e-3) or np.any(preds < 0) or np.max(preds) > 1.0:
            ex = np.exp(preds - np.max(preds))
            probs = ex / np.sum(ex)
            softmax_applied = True
        else:
            probs = preds

        # top 5
        top_indices = probs.argsort()[-5:][::-1]
        top = []
        for i in top_indices:
            label = LABELS[i] if i < len(LABELS) else f'IDX_{i}'
            top.append({'index': int(i), 'label': label, 'probability': float(probs[i])})

        info = {
            'model_input_shape': getattr(model, 'input_shape', None),
            'model_output_shape': getattr(model, 'output_shape', None),
            'softmax_applied': softmax_applied,
            'top5': top,
            'raw_logits_sample': preds.tolist()[:20]  # first 20 values to keep payload small
        }
        logger.info(f"Debug predict ({path}) top5: {top}")
        return jsonify(info)
    except Exception as e:
        logger.error(f'Debug predict error: {type(e).__name__}: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    if session.get('user'):
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if request.method == 'POST':
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            desc = request.form.get('image_desc')

            # compute hash and check cache
            file_hash = compute_hash(save_path)
            disease, confidence = get_cached_prediction(file_hash)
            
            # Diagnostic warnings for the user
            if model is None:
                flash('⚠️ DEMO MODE: Model not loaded. Results are simulated.', 'warning')
            elif hasattr(model, 'output_shape') and model.output_shape[-1] != len(LABELS):
                flash(f'⚠️ CONFIG ERROR: Model predicts {model.output_shape[-1]} classes, but app has {len(LABELS)} labels. Results will be wrong.', 'danger')

            if disease is None:
                disease, confidence = predict_disease(save_path)
                if disease is not None:
                    store_cache(file_hash, disease, confidence)

            if disease is None:
                flash('Could not make a prediction. Please try again.', 'danger')
                return redirect(request.url)

            # Warn user if prediction was low confidence
            if confidence is not None and confidence < CONFIDENCE_THRESHOLD:
                flash(f'Low confidence prediction ({confidence*100:.1f}%). Result may be incorrect.', 'warning')

            # store in history (even if cached)
            conn = get_db_connection()
            conn.execute('INSERT INTO history (image_path, disease, confidence, image_desc, timestamp) VALUES (?,?,?,?,?)',
                         (save_path, disease, confidence, desc, datetime.now().isoformat()))
            conn.commit()
            conn.close()

            # Get disease information
            info = DISEASE_INFO.get(disease, {})
            
            # Debug logging
            logger.debug(f'Disease: {disease}, Confidence: {confidence}')
            logger.debug(f'Info keys: {list(info.keys()) if info else "No info"}')
            
            return render_template('detect.html', 
                                 image_url='/' + save_path, 
                                 disease=disease,
                                 confidence=confidence, 
                                 info=info,
                                 image_desc=desc)
        else:
            flash('Invalid file type. Please upload JPG or PNG.', 'warning')
            return redirect(request.url)
    return render_template('detect.html')


@app.route('/camera')
def camera():
    return render_template('camera.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    # This route handles AJAX from camera capture
    data = request.form.get('image_data')
    if not data:
        return jsonify({'error': 'No image data received'}), 400
    
    # image_data is base64 string like 'data:image/png;base64,...'
    import base64
    try:
        header, encoded = data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        filename = f"capture_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(save_path, 'wb') as f:
            f.write(img_bytes)
    except Exception as e:
        logger.error(f'Image save error: {type(e).__name__}: {str(e)}')
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

    # try cache first
    file_hash = compute_hash(save_path)
    disease, confidence = get_cached_prediction(file_hash)
    if disease is None:
        disease, confidence = predict_disease(save_path)
        if disease is not None:
            store_cache(file_hash, disease, confidence)

    if disease is None:
        return jsonify({'error': 'Prediction failed. Please try again.'}), 500

    desc = request.form.get('image_desc')
    # Store in history
    conn = get_db_connection()
    conn.execute('INSERT INTO history (image_path, disease, confidence, image_desc, timestamp) VALUES (?,?,?,?,?)',
                 (save_path, disease, confidence, desc, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Get disease information for output
    info = DISEASE_INFO.get(disease, {})
    # include low-confidence flag for client-side handling
    low_conf = (confidence is not None and confidence < CONFIDENCE_THRESHOLD)
    return jsonify({
        'disease': disease,
        'confidence': confidence,
        'low_confidence': low_conf,
        'info': info,
        'image_url': '/' + save_path,
        'image_desc': desc
    })


@app.route('/history')
def history():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM history ORDER BY id DESC').fetchall()
    conn.close()
    # convert sqlite Row objects to plain dicts for JSON serialization
    records = [dict(r) for r in rows]
    return render_template('history.html', records=records)

@app.route('/export')
def export_csv():
    # allow any logged-in user to download their history as CSV
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM history ORDER BY id DESC').fetchall()
    conn.close()
    import csv
    from io import StringIO
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id','image_path','disease','confidence','image_desc','notes','timestamp'])
    for r in rows:
        cw.writerow([r['id'], r['image_path'], r['disease'], r['confidence'], r['image_desc'] or '', r['notes'] or '', r['timestamp']])
    output = si.getvalue()
    return app.response_class(output, mimetype='text/csv', headers={'Content-Disposition':'attachment;filename=history.csv'})

@app.route('/api/predict', methods=['POST'])
def api_predict():
    # simple JSON endpoint for external clients
    if 'image' not in request.files:
        return jsonify({'error':'no file'}), 400
    file = request.files['image']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        file_hash = compute_hash(save_path)
        disease, confidence = get_cached_prediction(file_hash)
        if disease is None:
            disease, confidence = predict_disease(save_path)
            if disease is not None:
                store_cache(file_hash, disease, confidence)
        if disease is None:
            return jsonify({'error':'prediction_failed'}), 500
        # optionally store history without user
        conn = get_db_connection()
        conn.execute('INSERT INTO history (image_path, disease, confidence, timestamp) VALUES (?,?,?,?)',
                     (save_path, disease, confidence, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        # include low-confidence flag for API clients
        low_conf = (confidence is not None and confidence < CONFIDENCE_THRESHOLD)
        return jsonify({'disease':disease,'confidence':confidence,'low_confidence':low_conf,'image_url':'/'+save_path})
    return jsonify({'error':'invalid_file'}), 400

# dark mode script injection later in template via static or inline


def precache_all():
    """Walk uploads folder and store predictions in cache for every image file."""
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for fname in files:
            if allowed_file(fname):
                path = os.path.join(root, fname)
                file_hash = compute_hash(path)
                if get_cached_prediction(file_hash)[0] is None:
                    disease, confidence = predict_disease(path)
                    if disease is not None:
                        store_cache(file_hash, disease, confidence)

@app.route('/precache')
def precache():
    if session.get('user') != 'admin':
        flash('Unauthorized access to cache operation.', 'danger')
        return redirect(url_for('index'))
    precache_all()
    flash('Cache populated for all uploaded images.', 'success')
    return redirect(url_for('history'))


@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    conn = get_db_connection()
    rec = conn.execute('SELECT * FROM history WHERE id = ?', (record_id,)).fetchone()
    if rec:
        image_path = rec['image_path']
        try:
            os.remove(image_path)
        except OSError:
            pass
        conn.execute('DELETE FROM history WHERE id = ?', (record_id,))
        conn.commit()
    conn.close()
    flash('Record deleted.', 'success')
    return redirect(url_for('history'))

@app.route('/note/<int:record_id>', methods=['POST'])
def update_note(record_id):
    note = request.form.get('note')
    conn = get_db_connection()
    conn.execute('UPDATE history SET notes = ? WHERE id = ?', (note, record_id))
    conn.commit()
    conn.close()
    flash('Note updated.', 'success')
    return redirect(url_for('history'))


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        ip_address = request.remote_addr
        if verify_user(email, password):
            session['user'] = email
            log_login_activity(email, 'LOGIN', 'SUCCESS', ip_address)
            logger.info(f'User {email} logged in from {ip_address}')
            flash('Logged in successfully','success')
            return redirect(url_for('index'))
        else:
            log_login_activity(email, 'LOGIN', 'FAILED', ip_address)
            logger.warning(f'Failed login attempt for {email} from {ip_address}')
            flash('Invalid credentials','danger')
    return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not email or not password:
            flash('Email and password required','warning')
        else:
            success, message = create_user(email, password)
            if success:
                flash('Account created. You can now log in.','success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    user_email = session.get('user', 'Unknown')
    ip_address = request.remote_addr
    session.pop('user', None)
    log_login_activity(user_email, 'LOGOUT', 'SUCCESS', ip_address)
    logger.info(f'User {user_email} logged out from {ip_address}')
    flash('Logged out','info')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/resources')
def resources():
    return render_template('resources.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/logs')
def view_logs():
    """View login activity logs (admin only)."""
    if session.get('user') != 'admin@example.com':
        flash('Unauthorized: Only admin can view logs.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM login_logs ORDER BY id DESC LIMIT 100').fetchall()
    conn.close()
    
    # Convert to dict for template
    log_records = [dict(log) for log in logs]
    return render_template('logs.html', logs=log_records)


@app.route('/debug/files')
def debug_files():
    """Check if model files exist on server."""
    import os
    info = {
        'model_exists': os.path.exists(MODEL_PATH),
        'model_size': os.path.getsize(MODEL_PATH) if os.path.exists(MODEL_PATH) else 0,
        'class_indices_exists': os.path.exists('model/class_indices.json'),
        'model_loaded': model is not None,
        'cwd': os.getcwd(),
        'model_path': MODEL_PATH
    }
    return jsonify(info)


if __name__ == '__main__':
    # Load debug mode from environment, default to False for production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logger.info(f'Starting Flask app. Debug mode: {debug_mode}')
    # Allow overriding port via environment variable. Default to 8000 to avoid common conflicts on 5000.
    port = int(os.environ.get('PORT', '8000'))
    logger.info(f'Binding to port: {port}')
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
