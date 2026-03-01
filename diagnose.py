#!/usr/bin/env python
"""
Diagnostic script to verify the AI Crop Disease Detection System setup
Run this before starting the application
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("AI Crop Disease Detection System - Diagnostic Check")
print("=" * 60)

# Check Python version
print(f"\n[OK] Python Version: {sys.version.split()[0]}")

# Check required directories
project_dir = Path(__file__).parent
required_dirs = [
    'model',
    'static',
    'static/css',
    'static/js',
    'static/images',
    'static/uploads',
    'templates',
    'database'
]

print("\n[*] Checking directories...")
for dir_path in required_dirs:
    full_path = project_dir / dir_path
    if full_path.exists():
        print(f"  [OK] {dir_path}/")
    else:
        print(f"  [X] {dir_path}/ - MISSING")
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"    --> Created")

# Check required files
required_files = [
    'app.py',
    'requirements.txt',
    'Dockerfile',
    'README.md',
    'static/css/style.css',
    'static/js/main.js',
    'static/js/camera.js',
    'templates/base.html',
    'templates/index.html',
    'templates/detect.html',
    'templates/camera.html',
    'templates/history.html',
    'templates/resources.html',
    'templates/about.html',
    'templates/contact.html'
]

print("\n[*] Checking files...")
for file_path in required_files:
    full_path = project_dir / file_path
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"  [OK] {file_path} ({size:,} bytes)")
    else:
        print(f"  [X] {file_path} - MISSING")

# Check Python imports
print("\n[*] Checking Python dependencies...")
required_packages = [
    'flask',
    'tensorflow',
    'numpy',
    'pillow',
    'cv2',  # opencv-python
    'werkzeug'
]

missing_packages = []
for package in required_packages:
    try:
        if package == 'cv2':
            import cv2
        elif package == 'pillow':
            from PIL import Image
        else:
            __import__(package)
        print(f"  [OK] {package}")
    except ImportError:
        print(f"  [X] {package} - NOT INSTALLED")
        missing_packages.append(package)

if missing_packages:
    print(f"\n[!] Missing packages: {', '.join(missing_packages)}")
    print("   Run: pip install -r requirements.txt")

# Check disease database
print("\n[*] Checking disease database...")
try:
    sys.path.insert(0, str(project_dir))
    from app import DISEASE_INFO, LABELS
    
    diseases = list(DISEASE_INFO.keys())
    print(f"  [OK] {len(diseases)} diseases loaded:")
    for disease in diseases:
        info = DISEASE_INFO[disease]
        has_products = 'products' in info and info['products']
        products_status = "[OK] products" if has_products else "[X] no products"
        print(f"    - {disease} ({products_status})")
except Exception as e:
    print(f"  [X] Error loading disease database: {e}")

# Check Keras model
print("\n[*] Checking AI model...")
model_path = project_dir / 'model' / 'crop_model.h5'
if model_path.exists():
    print(f"  [OK] Model found: {model_path}")
    
    # Verify model architecture matches labels
    try:
        print("  [*] Verifying model architecture...")
        import tensorflow as tf
        # Suppress TF logs
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        model = tf.keras.models.load_model(model_path)
        
        input_shape = model.input_shape
        print(f"  [INFO] Model expects input shape: {input_shape}")
        
        output_classes = model.output_shape[-1]
        if output_classes == len(LABELS):
            print(f"  [OK] Model output ({output_classes} classes) matches configuration.")
        else:
            print(f"  [!] MISMATCH: Model has {output_classes} outputs, but app.py has {len(LABELS)} labels.")
            print(f"      --> You must update 'LABELS' list in app.py to match your model.")
    except Exception as e:
        print(f"  [!] Warning: Could not verify model: {e}")
else:
    print(f"  [*] Model not found (Demo mode will be used)")
    print(f"     Add model to: model/crop_model.h5")

# Final summary
print("\n" + "=" * 60)
print("[OK] Diagnostic check complete!")
print("="*60)

if missing_packages:
    print("\n[!] ACTION NEEDED:")
    print("   Run: pip install -r requirements.txt")
else:
    print("\n[OK] All systems ready!")
    print("   Run: python app.py")
    print("   Then visit: http://localhost:5000")

print("\n" + "=" * 60)
