# AI Crop Disease Detection System

This project is a professional AI-powered web application designed for detecting plant leaf diseases using a trained CNN Keras model. It is built with Flask, Bootstrap, and integrates a TensorFlow/Keras model.

## 🚀 Features

- Image upload and detection
- Live camera (webcam) detection
- User registration/login with animated pages and dark-mode toggle
- Disease history storage with searchable/filterable table, notes editing, and CSV export
- Admin panel actions (pre‑cache dataset, cache optimization)
- Dataset gallery displaying all uploaded images
- Integrated language translation via Google Translate widget
- API endpoint (`/api/predict`) for mobile or external use
- Dark mode support and animated login screen for polish
- Caching of predictions to speed up repeat images
- Clean two‑column dashboard layout for results

## 🔧 Tech Stack

- **Backend:** Python Flask
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **ML:** TensorFlow / Keras (.h5 model)
- **Database:** SQLite
- **Deployment:** Docker-ready (Render/Railway/AWS/GCP)

## 📁 Project Structure

Additional endpoints:
- `/login`, `/register` – user authentication
- `/history` – view past detections with charts and export
- `/precache` – admin cache job
- `/api/predict` – JSON prediction API


```
project/
│
├── model/
│   └── crop_model.h5        # Place your trained model here
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/             # Uploaded images stored here
├── templates/
├── database/
│   └── data.db              # SQLite database (auto-created)
├── app.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🛠 Setup Instructions

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd project
   ```
2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Place your trained model**
   - Copy your Keras model (`.h5`) into `model/crop_model.h5`.
5. **Run the application**
   ```bash
   python app.py
   ```
6. **Open browser**
   - Visit `http://localhost:5000`

## ☁️ Deployment

- Build Docker image:
  ```bash
  docker build -t crop-disease-app .
  ```
- Run container:
  ```bash
  docker run -p 5000:5000 crop-disease-app
  ```

Deployment steps for Render/Railway/AWS/GCP can be extended in documentation.

## ✅ Notes

- Ensure model input size 224x224 and normalized
- SQLite database created on first run

## 📸 Sample Images

Place your test images under `static/images/` for quick access.

---
Final year project submission ready! 🎓
