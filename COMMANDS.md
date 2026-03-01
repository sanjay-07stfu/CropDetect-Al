# 🚀 Command Reference Guide

## Quick Command Cheat Sheet

### **🎯 Start Application (Pick One)**

#### **EASIEST - One Command Start**
```bash
python start.py
```
✅ Does everything automatically:
- Installs dependencies
- Verifies setup
- Starts application
- Opens browser

---

#### **STEP-BY-STEP - Manual Setup**
```bash
# Step 1: Install dependencies (2-3 minutes)
pip install -r requirements.txt

# Step 2: Verify everything is set up
python diagnose.py

# Step 3: Start the application
python app.py
```

Then open: **http://localhost:5000**

---

## 📋 All Available Commands

### **Getting Started**
| Command | What It Does | Time |
|---------|-------------|------|
| `python start.py` | Install + verify + start | 3-5 min |
| `python diagnose.py` | Check setup without starting | 1 min |
| `pip install -r requirements.txt` | Install dependencies only | 2-3 min |

### **Running the App**
| Command | What It Does | When to Use |
|---------|-------------|------------|
| `python app.py` | Start app (demo mode) | After dependencies installed |
| `python app.py --port 5001` | Start on different port | If 5000 already in use |
| `python -m flask run` | Alternative Flask command | If app.py doesn't work |

### **Verification & Testing**
| Command | What It Does | Purpose |
|---------|-------------|---------|
| `python diagnose.py` | Verify all components | Check before starting |
| `pip list` | Show installed packages | Verify dependencies |
| `python --version` | Check Python version | Should be 3.8+ |

### **Docker Commands**
| Command | What It Does | Use Case |
|---------|-------------|----------|
| `docker build -t crop-disease .` | Build Docker image | Deployment preparation |
| `docker run -p 5000:5000 crop-disease` | Run in Docker | Production deployment |

---

## 🔍 Troubleshooting Commands

### **Port Already in Use**
```bash
# Option 1: Use different port (Edit app.py)
python app.py  # Then change port in app.py before running

# Option 2: Kill process on port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Option 3: Use different port in Flask
python -m flask run --port 5001
```

### **Dependencies Issues**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install specific version of dependency
pip install Flask==2.2.5

# Reinstall all from scratch
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### **JavaScript/CSS Not Loading**
```bash
# Clear browser cache (Ctrl+Shift+Delete) then refresh

# Or in Python, clear temporary files:
# Delete all .pyc files:
python -m py_compile app.py
```

---

## 🎬 Testing Sequence

### **Test 1: Verify Installation**
```bash
python diagnose.py
# Should show: "✅ All systems ready!"
```

### **Test 2: Start Application**
```bash
python app.py
# Should show: "Running on http://127.0.0.1:5000"
```

### **Test 3: Open in Browser**
```
In web browser, go to: http://localhost:5000
# Should see homepage with green theme
```

### **Test 4: Upload Image**
```
1. Click "Try Detection" button
2. Select any image file
3. Should show disease result + products
```

### **Test 5: Test Camera**
```
1. Go to "Camera" tab
2. Allow camera permission
3. Click "Start Camera"
4. Click "Capture & Analyze"
```

---

## 📊 Platform-Specific Commands

### **Windows (PowerShell)**
```powershell
# Start app
python start.py

# Or manual:
python -m pip install -r requirements.txt
python app.py
```

### **Mac/Linux (Terminal)**
```bash
# Start app
python3 start.py

# Or manual:
python3 -m pip install -r requirements.txt
python3 app.py
```

### **VS Code Terminal**
```bash
# Integrated terminal - just use:
python start.py
# (Works on all platforms automatically)
```

---

## 🐛 Debug Mode Commands

### **Enable Flask Debug Logging**
Edit `app.py` and change:
```python
if __name__ == '__main__':
    app.run(debug=True)  # Already enabled!
```

### **Check Specific Endpoint**
```bash
# Check if server is running:
curl http://localhost:5000/

# Test detection API:
curl -X POST http://localhost:5000/detect-image -F "image=@image.jpg"
```

### **View Database**
```bash
# Use Python to inspect database
python -c "
import sqlite3
conn = sqlite3.connect('database/detections.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM history')
for row in cursor:
    print(row)
"
```

---

## 📱 Mobile Testing Commands

### **Access from Phone on Same Network**
Find your computer's IP:
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig
```

Then on phone, go to:
```
http://YOUR_IP:5000
```

Example: `http://192.168.1.100:5000`

---

## 🔄 Workflow Commands

### **Development Workflow**
```bash
# 1. Start application
python start.py

# 2. Make code changes (in editor)

# 3. Reload browser (auto-refreshes with debug=True)
# Press F5 in browser

# 4. Check for errors
# Look at Python console output from step 1
```

### **If Model Doesn't Load**
```bash
# 1. Place model file
# Copy your crop_model.h5 to model/ folder

# 2. Restart app
# Stop Python (Ctrl+C), then:
python app.py

# 3. Application should now use your model
# Check homepage for confirmation
```

---

## 📈 Production Commands

### **Before Deployment**
```bash
# 1. Test everything locally
python start.py
# Visit http://localhost:5000
# Test all features

# 2. Check dependencies
pip freeze > deployed_requirements.txt

# 3. Verify Docker setup
docker build -t crop-disease .
docker run -p 5000:5000 crop-disease
```

### **Deploy to Cloud**
```bash
# Example: Render.com
# (Full instructions in README_COMPLETE.md)

# 1. Commit to GitHub
git add .
git commit -m "Ready for production"
git push

# 2. Connect to Render
# (Follow Render documentation)
```

---

## ⚡ Quick Reference

### **Three Ways to Start**

**Fastest** (1 click):
```bash
python start.py
```

**Manual** (full control):
```bash
pip install -r requirements.txt
python app.py
```

**Docker** (production):
```bash
docker build -t crop-disease .
docker run -p 5000:5000 crop-disease
```

---

## 🆘 Emergency Commands

### **If Everything Breaks**
```bash
# 1. Stop app (Ctrl+C in terminal)

# 2. Delete Python cache
python -m py_compile app.py

# 3. Reinstall dependencies from scratch
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 4. Start fresh
python diagnose.py
python app.py
```

### **If Browser Shows Errors**
```bash
# 1. Clear browser cache
# Ctrl+Shift+Delete (Chrome/Edge)
# Cmd+Shift+Delete (Mac)

# 2. Try different browser
# Chrome recommended

# 3. Check browser console
# Press F12, click Console tab
# Look for red errors
```

### **If Port is Stuck**
```bash
# Find and kill process on port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID 1234 /F

# Mac/Linux:
lsof -i :5000
kill -9 <PID>

# Then try different port:
python -m flask run --port 5001
```

---

## 📞 Getting Help

If a command doesn't work:

1. **Check file exists**:
   ```bash
   # On Windows
   dir app.py
   dir requirements.txt
   
   # On Mac/Linux
   ls app.py
   ls requirements.txt
   ```

2. **Run diagnostic**:
   ```bash
   python diagnose.py
   ```

3. **Check Python version**:
   ```bash
   python --version
   # Should be 3.8 or higher
   ```

4. **Check pip**:
   ```bash
   pip --version
   ```

5. **Read error output carefully** - Python errors are usually descriptive!

---

## ✅ Command Checklist

Before starting:
- [ ] Windows/Mac/Linux ready
- [ ] Python 3.8+ installed
- [ ] In correct directory: `c:\Users\yedag\OneDrive\Desktop\new project`
- [ ] Can see all files listed in file explorer
- [ ] Terminal/PowerShell open in that directory

Ready to start?

### **Run this one command**:
```bash
python start.py
```

✨ That's it! Enjoy your AI Crop Disease Detection System! 🌾
