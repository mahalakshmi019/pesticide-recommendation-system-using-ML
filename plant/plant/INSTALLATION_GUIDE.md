# PlantGuard - Installation Guide

PlantGuard is a web-based plant disease detection system that uses AI and image processing to identify plant diseases and provide alerts to users.

## Table of Contents
- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **Processor**: Intel Core i5 or equivalent (or better)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free disk space
- **Internet**: Required for initial setup and real-time features

### Operating System
- Windows 10/11
- macOS 10.14+
- Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+)

---

## Prerequisites

Before installing PlantGuard, ensure you have the following installed:

### 1. **Python 3.8 or Higher**
   - Download from: https://www.python.org/downloads/
   - During installation, **check "Add Python to PATH"**
   - Verify installation:
     ```powershell
     python --version
     ```

### 2. **MySQL Server 5.7 or Higher** or Xampp
   - Download from: https://www.mysql.com/downloads/
   - Download MySQL Community Server
   - Install and note your **username** and **password** (default: root/root)
   - Verify installation:
     ```powershell
     mysql --version
     ```

  ```

---

## Installation Steps

### Step 1: Extract/Download the Project

**Option A: Using Git**
```powershell
git clone <repository-url>
cd plant
```

**Option B: Manual Download**
- Download the project ZIP file
- Extract it to your desired location
- Open PowerShell in the extracted folder

### Step 2: Create Python Virtual Environment

Navigate to the project directory and create a virtual environment:

```powershell
python -m venv venv
```

Activate the virtual environment:

**On Windows:**
```powershell
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 3: Install Python Dependencies

With the virtual environment activated, install all required packages:

```powershell
pip install -r requirements.txt
```

This will install:
- **Flask**: Web framework
- **mysql-connector-python**: MySQL database connector
- **opencv-python**: Image processing library
- **Werkzeug**: Utility library for Flask
- **Jinja2**: Template engine

---

## Database Setup

### Step 1: Start MySQL Service

**On Windows:**
```powershell
# If MySQL is installed as a service
net start MySQL80
```

**On macOS:**
```bash
brew services start mysql
```

**On Linux:**
```bash
sudo service mysql start
```

### Step 2: Connect to MySQL

Open MySQL command line:

```powershell
mysql -u root -p
```

Enter your MySQL password when prompted.

### Step 3: Create Database and Import Schema

Inside MySQL shell, run:

```sql
CREATE DATABASE plants_db;
USE plants_db;
```

Exit MySQL and import the database schema:

```powershell
mysql -u root -p plantguard < database.sql
```

Enter your MySQL password when prompted.

### Step 4: Verify Database Creation

Connect to MySQL again:

```powershell
mysql -u root -p plantguard
```

Run:

```sql
SHOW TABLES;
```

You should see these 7 tables:
- alerts
- complaints
- notifications
- predictions
- user_alerts
- users
- user_stats (view)

---

## Configuration

### Step 1: Update Database Connection

Open `config.py` and verify the MySQL connection settings:

```python
class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your_password'  # Change to your MySQL password
    MYSQL_DATABASE = 'plantguard'
```

**Update these values if:**
- Your MySQL username is not `root`
- Your MySQL password is different
- Your MySQL server is on a different host

### Step 2: Create Upload Directory

The application needs a directory for image uploads:

```powershell
mkdir static\uploads
```

### Step 3: Verify File Structure

Ensure your project has this structure:

```
plant/
├── app.py
├── config.py
├── database.sql
├── image_processor.py
├── requirements.txt
├── INSTALLATION_GUIDE.md
├── static/
│   ├── uploads/
│   ├── notifications.js
│   ├── service-worker.js
│   ├── styles/
│   │   ├── admin.css
│   │   └── user.css
│   └── notifications.js
├── templates/
│   ├── index.html
│   ├── admin/
│   │   ├── adminlogin.html
│   │   ├── alert.html
│   │   ├── dashboard.html
│   │   └── history.html
│   └── user/
│       ├── complaint.html
│       ├── notifications.html
│       ├── predict.html
│       ├── result.html
│       ├── useralerts.html
│       ├── userlogin.html
│       └── usersignup.html
└── venv/
```

---

## Running the Application

### Step 1: Activate Virtual Environment

**On Windows:**
```powershell
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 2: Start the Flask Application

```powershell
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 3: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

Or:
```
http://127.0.0.1:5000
```

---

## First-Time Setup

### Create Admin Account

1. Access the home page: `http://localhost:5000`
2. Click **"Admin Login"**
3. Click **"Create Admin Account"** (if signup link is available)
4. Fill in:
   - Full Name: Your name
   - Email: your-email@example.com
   - Phone: Your phone number
   - Password: Your secure password
5. Click **"Create Account"**

### Create User Account

1. From home page, click **"User Login"**
2. Click **"Sign Up"**
3. Fill in your details
4. Click **"Sign Up"**

---

## Features Overview

### User Features
- 📷 Upload plant images for disease detection
- 🔍 Get instant disease diagnosis with severity scores
- 📊 View detection history
- 🚨 Receive disease alerts from admins
- 🔔 Browser notifications for real-time alerts
- 💬 Submit support tickets and feedback

### Admin Features
- 📈 Dashboard with statistics and user activity
- 👥 View all user detection history
- 🖼️ Preview uploaded plant images
- 🔔 Send disease alerts to users
- 📋 Manage user complaints and feedback
- 🎯 Track alert delivery status

### Notification System
- 🔔 Real-time browser notifications
- ⏱️ 5-second polling for new alerts
- 📲 Persistent notification display
- ✅ Notification read tracking

---

## Troubleshooting

### Issue 1: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
- Ensure virtual environment is activated (you should see `(venv)` in terminal)
- Reinstall requirements:
  ```powershell
  pip install -r requirements.txt
  ```

### Issue 2: "Access denied for user 'root'@'localhost'"

**Solution:**
- Check MySQL is running:
  ```powershell
  mysql -u root -p
  ```
- Update `config.py` with correct credentials
- Ensure MySQL service is started

### Issue 3: "Unknown database 'plantguard'"

**Solution:**
- Create the database manually:
  ```powershell
  mysql -u root -p < database.sql
  ```
- Verify import was successful:
  ```powershell
  mysql -u root -p plantguard -e "SHOW TABLES;"
  ```

### Issue 4: "Port 5000 already in use"

**Solution:**
- Stop any other Flask applications
- Or run on a different port:
  ```powershell
  python -c "import os; os.environ['FLASK_ENV']='development'; exec(open('app.py').read())"
  ```
- Or modify `app.py` to use a different port:
  ```python
  app.run(debug=True, port=5001)
  ```

### Issue 5: Notifications not popping up

**Solution:**
1. Check browser notification permissions:
   - Click on notifications bell in your browser
   - Ensure notifications are allowed for localhost:5000
2. Check browser console for errors (F12 → Console tab)
3. Verify notification polling is working:
   - Open browser console
   - You should see messages starting with `[PlantCare]`
4. Check if /api/notifications/list endpoint is returning data:
   - Go to http://localhost:5000/api/notifications/list
   - You should see JSON response with notifications

### Issue 6: Images not uploading

**Solution:**
- Ensure `static/uploads` directory exists:
  ```powershell
  mkdir static\uploads
  ```
- Check file permissions
- Verify image size is under 50MB
- Check browser console for upload errors

### Issue 7: Admin can't send alerts

**Solution:**
1. Verify admin is logged in
2. Check MySQL notifications table exists:
   ```powershell
   mysql -u root -p plantguard -e "SHOW TABLES;"
   ```
3. Verify user accounts exist in database:
   ```powershell
   mysql -u root -p plantguard -e "SELECT * FROM users;"
   ```
4. Check app.py logs for errors

---

## Performance Optimization

### For Production Deployment

1. **Disable Debug Mode** in `app.py`:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use Production Server** (Gunicorn on Linux/macOS):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Optimize Database Queries**:
   - Ensure all indices are created
   - Monitor slow queries

4. **Enable HTTPS**:
   - Use Let's Encrypt certificates
   - Configure SSL in Flask

5. **Scale Uploads Directory**:
   - Consider cloud storage (AWS S3, Azure Blob)
   - Implement cleanup of old images

---

## Security Considerations

1. **Change Default Credentials**: Update MySQL password
2. **Database Backups**: Regularly backup your `plantguard` database
3. **Session Security**: Keep Flask secret key secure
4. **Input Validation**: All inputs are validated server-side
5. **HTTPS**: Use HTTPS in production
6. **Rate Limiting**: Consider implementing rate limiting for APIs

---

## Support & Documentation

For more information:
- **Flask Documentation**: https://flask.palletsprojects.com/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **OpenCV Documentation**: https://docs.opencv.org/

---

## License

This project is proprietary. All rights reserved.

---

## Version

**PlantGuard v1.0.0**
Last Updated: December 4, 2025

---

Happy gardening! 🌱
