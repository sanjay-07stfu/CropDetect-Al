# Quick Start & Testing Guide

## Installation & Setup

```bash
# Navigate to project folder
cd "c:\Users\yedag\OneDrive\Desktop\new project"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

Then open: **http://localhost:5000**

---

## Testing the Application

### ✅ Without a Trained Model (Demo Mode)

If you don't have a trained model yet, the application will automatically run in **Demo Mode**:
- Each image upload returns a **random disease prediction** from the list
- Full disease descriptions are displayed
- All supplement & fungicide product links are shown
- Perfect for testing UI and functionality

### Features to Test:

1. **Upload Detection Page** (`/detect`)
   - Click "Upload Leaf Image" or drag & drop an image
   - View disease prediction with confidence %
   - Read disease description & prevention tips
   - See recommended supplements & fungicide links
   - Expand accordion sections for each category

2. **Live Camera Page** (`/camera`)
   - Click "Capture & Analyze"
   - View results in real-time
   - See product recommendations directly

3. **History Page** (`/history`)
   - View all past predictions
   - Filter by disease name
   - See confidence scores & timestamps
   - Delete records you don't need

4. **Resources Page** (`/resources`)
   - Browse all available products by category
   - Supplements, Fungicides, Pesticides, Tools
   - Educational resources and forums

---

## 🚀 Using a Real Trained Model

To enable production mode with actual predictions:

1. **Train or download a Keras model** that classifies plant diseases
2. **Save it as**: `model/crop_model.h5`
3. **Update in app.py if model classes differ from these diseases:**
   - Powdery Mildew
   - Leaf Spot
   - Early Blight
   - Late Blight
   - Rust

4. **Restart the application** - it will auto-detect and load the model

---

## Troubleshooting

### ❌ "Could not make prediction"
- **Cause**: Model not loaded or invalid image format
- **Solution**: Check console for errors; ensure JPG/PNG format

### ❌ "No descriptions showing"
- **Cause**: Disease name doesn't match DISEASE_INFO keys
- **Solution**: Check console logs to see predicted disease name

### ❌ "Camera not working"
- **Cause**: Browser permission not granted
- **Solution**: Allow camera access when promted

### ✅ How to verify it's working:

Look for these logs in your terminal:
```
[DEMO MODE] Predicted: Powdery Mildew (85.23% confidence)
Disease: Powdery Mildew
Confidence: 0.8523
Info keys: ['description', 'prevention', 'organic', 'chemical', 'precautions', 'products']
Products found: {'supplements': [...], 'fungicides': [...]}
```

If you see these logs, the system is working correctly! ✅

---

## File Structure

```
project/
├── app.py                 ← Main Flask application
├── requirements.txt       ← Python dependencies
├── Dockerfile            ← Docker configuration
├── model/
│   └── crop_model.h5     ← Your trained model (optional)
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   ├── js/camera.js
│   └── uploads/          ← Uploaded images stored here
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── detect.html       ← Image upload page
│   ├── camera.html       ← Live camera page
│   ├── history.html      ← Past predictions
│   ├── resources.html    ← Product catalog
│   ├── about.html
│   └── contact.html
└── database/
    └── data.db           ← SQLite (auto-created)
```

---

## Features Included

✅ Image upload disease detection
✅ Live camera detection  
✅ Disease history storage & search
✅ Product recommendations (supplements, fungicides)
✅ Direct Amazon product links
✅ Professional UI with animations
✅ Mobile responsive design
✅ Toast notifications
✅ Demo mode (no model required)
✅ Demo mode testing

Enjoy! 🌾
