# Login Activity Logs - User Guide

## 📋 Overview

Your AI Crop Disease Detection System now has a **complete login audit logging system**. This tracks all user login and logout activities, including:

- ✅ Email address of the user
- ✅ Type of action (LOGIN or LOGOUT)
- ✅ Status (SUCCESS or FAILED)
- ✅ Exact timestamp when the action occurred
- ✅ IP address of the user

---

## 🔐 How Login Logging Works

### **Automatic Logging**

Every time a user attempts to log in, the system automatically logs:

```
User Login Attempt
├─ Email: user@example.com
├─ Action: LOGIN
├─ Status: SUCCESS (or FAILED)
├─ Timestamp: 2026-03-05T14:30:45.123456
└─ IP Address: 192.168.1.100
```

### **Where Logs Are Stored**

The logs are stored in your SQLite database in a table called **`login_logs`** with the following structure:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | INTEGER | Unique identifier |
| `email` | TEXT | User email address |
| `action` | TEXT | LOGIN or LOGOUT |
| `status` | TEXT | SUCCESS or FAILED |
| `timestamp` | TEXT | ISO format timestamp |
| `ip_address` | TEXT | Client's IP address |

**Database location:** `database/data.db`

---

## 👤 Admin Account Credentials

By default, the system creates an admin account with these credentials:

```
Email: admin@example.com
Password: password
```

⚠️ **IMPORTANT:** Change this password before showing to examiners!

To change admin password:
1. Delete existing `database/data.db`
2. Share new credentials with authorized users only

---

## 📊 Viewing Login Logs

### **Step 1: Login as Admin**

1. Click **"Login"** button in the navigation bar
2. Enter credentials:
   - **Email:** `admin@example.com`
   - **Password:** `password`

### **Step 2: Access Logs Page**

After logging in as admin, a new menu item appears:

```
Navigation Bar → "Admin Logs" 
```

Click **"Admin Logs"** to view the login activity page.

### **Step 3: Review Login Activity**

The logs page displays:

- **Activity Statistics Cards:**
  - Total Activities
  - Successful Logins
  - Failed Attempts
  - Total Logouts

- **Detailed Activity Table:**
  - Log number
  - Email address
  - Action (LOGIN/LOGOUT with icons)
  - Status (SUCCESS/FAILED)
  - Timestamp
  - IP Address

- **Summary Statistics:**
  - Total recorded activities
  - Unique users count
  - First activity timestamp
  - Latest activity timestamp

---

## 🔍 Examples of Logged Activities

### **Successful Login**
```
ID: 5
Email: farmer@gmail.com
Action: LOGIN (green badge)
Status: SUCCESS (green badge)
Timestamp: 2026-03-05T14:30:45.123456
IP: 192.168.1.50
```

### **Failed Login Attempt**
```
ID: 4
Email: farmer@gmail.com
Action: LOGIN
Status: FAILED (red badge)
Timestamp: 2026-03-05T14:29:10.654321
IP: 192.168.1.50
```

### **Logout**
```
ID: 6
Email: farmer@gmail.com
Action: LOGOUT (gray badge)
Status: SUCCESS (green badge)
Timestamp: 2026-03-05T14:35:00.999999
IP: 192.168.1.50
```

---

## 📈 Log Statistics & Analytics

The logs page displays useful statistics:

### **Activity Cards**
- **Total Activities:** Count of all login/logout records
- **Successful Logins:** Number of successful authentication attempts
- **Failed Attempts:** Number of unsuccessful login tries
- **Total Logouts:** Number of logout events

### **Summary Section**
- Total recorded activities (last 100 entries shown)
- Number of unique users
- First activity date/time
- Latest activity date/time

---

## 🔒 Security Features

### **Only Admin Can View Logs**
- Non-admin users cannot access `/logs` page
- Unauthorized access shows error message
- Access attempts are logged

### **What's Tracked**
- All login attempts (successful AND failed)
- All logout events
- User's IP address
- Exact timestamp to the microsecond
- Status of each attempt

### **Data Integrity**
- Passwords are NOT logged (only hashed in users table)
- Logs cannot be deleted from UI (only from database)
- Immutable audit trail for security

---

## 💡 Use Cases

### **For Project Examiners:**
1. Verify user authentication system works
2. See audit trail of who logged in when
3. Check security features (failed attempts logged)
4. Demonstrate system reliability

### **For Administrators:**
1. Troubleshoot login issues
2. Track suspicious failed attempts
3. Monitor system usage patterns
4. Create audit reports for compliance

### **For Farmers/Users:**
1. Users cannot see logs (privacy protected)
2. Only admin can access audit trail
3. Encourages responsible system usage

---

## 🛠️ Database Access (Advanced)

### **View Raw Logs Using SQLite**

If you want to see the raw database:

```bash
# Open database
sqlite3 database/data.db

# View all login logs
SELECT * FROM login_logs ORDER BY id DESC;

# View only failed attempts
SELECT * FROM login_logs WHERE status='FAILED';

# View login history for specific user
SELECT * FROM login_logs WHERE email='admin@example.com' ORDER BY timestamp DESC;

# Count logins per user
SELECT email, COUNT(*) as login_count FROM login_logs WHERE action='LOGIN' GROUP BY email;
```

### **Export Logs to CSV**

```bash
sqlite3 -header -csv database/data.db "SELECT * FROM login_logs;" > login_logs.csv
```

---

## 📝 Code Implementation Details

### **Log Function in app.py**

```python
def log_login_activity(email, action, status, ip_address=None):
    """Log user login/logout activity to audit table."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO login_logs (email, action, status, timestamp, ip_address) VALUES (?, ?, ?, ?, ?)',
        (email, action, status, datetime.now().isoformat(), ip_address)
    )
    conn.commit()
    conn.close()
```

### **Login Route with Logging**

```python
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        ip_address = request.remote_addr
        
        if verify_user(email, password):
            session['user'] = email
            log_login_activity(email, 'LOGIN', 'SUCCESS', ip_address)  # ← Logged
            flash('Logged in successfully','success')
            return redirect(url_for('index'))
        else:
            log_login_activity(email, 'LOGIN', 'FAILED', ip_address)  # ← Logged
            flash('Invalid credentials','danger')
    return render_template('login.html')
```

---

## ⚠️ Troubleshooting

### **Admin Logs Link Not Showing**

**Problem:** You logged in but the "Admin Logs" link doesn't appear in navbar

**Solution:**
- Ensure you're logged in as `admin@example.com`
- Check browser console for errors
- Clear browser cache and reload

### **Cannot Access Logs Page**

**Problem:** Error message: "Unauthorized: Only admin can view logs"

**Solution:**
- You must be logged in as admin
- Use email: `admin@example.com`
- Check that session is active (not expired)

### **Logs Not Being Recorded**

**Problem:** No activity appears in logs page

**Solution:**
- Make sure app.py is running
- Check database permissions
- Verify database/data.db file exists
- Restart the application

---

## 📌 Quick Reference

### **Key URLs**

| URL | Purpose | Who Can Access |
|-----|---------|-----------------|
| `/login` | Login page | Everyone |
| `/logout` | Logout | Logged-in users |
| `/logs` | View activity logs | Admin only |

### **Admin User**

- **Email:** `admin@example.com`
- **Password:** `password`
- **Role:** Can view login logs
- **Access:** Link only shows when logged in as admin

### **Log Table Columns**

1. **id** - Sequential record number
2. **email** - User's email address
3. **action** - LOGIN or LOGOUT
4. **status** - SUCCESS or FAILED
5. **timestamp** - When it happened
6. **ip_address** - User's IP address

---

## 🎯 For Your Presentation

### **What to Show Examiners**

1. **Login System Works:**
   - Register a test user
   - Login with test user
   - Show it in logs

2. **Security Features:**
   - Attempt invalid login
   - Show "FAILED" status in logs
   - Explain encryption/hashing

3. **Admin Panel:**
   - Login as admin
   - Click "Admin Logs"
   - Show comprehensive activity log
   - Explain tracked information

4. **Statistics:**
   - Show activity summary cards
   - Explain data integrity
   - Discuss security implications

### **Example Presentation Dialogue**

> "Our system includes a comprehensive login audit system. Every user action is logged with timestamp and IP address. Examiners can login as admin to review who accessed the system and when. Here you can see all login attempts, including failed ones, which is important for security and compliance."

---

## 📚 Additional Resources

- **Main README:** See `README.md` for full project overview
- **Quick Start:** See `QUICKSTART.md` for setup instructions
- **Database Guide:** SQLite documentation at https://www.sqlite.org/

---

**Last Updated:** March 5, 2026  
**System Version:** 1.0 with Login Audit Logging
