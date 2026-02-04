from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
load_dotenv()
import mysql.connector
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config
from image_processor import analyze_plant_health

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection with error handling"""
    try:
        return mysql.connector.connect(
            host=app.config['MYSQL_HOST'], 
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'], 
            database=app.config['MYSQL_DB']
        )
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        raise

@app.route('/')
def index(): 
    return render_template('index.html')

# --- AUTH ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.json
            if not data.get('email') or not data.get('password'):
                return jsonify({'success': False, 'message': 'Email and password required'})
            
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (data['email'], data['password']))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['fullname'] = user['fullname']
                redirect_url = '/admin/dashboard' if user['role'] == 'admin' else '/predict'
                return jsonify({'success': True, 'redirect': redirect_url})
            return jsonify({'success': False, 'message': 'Invalid email or password'})
        except Exception as e:
            logger.error(f"Login Error: {e}")
            return jsonify({'success': False, 'message': 'Server Error. Please try again.'})
    return render_template('user/userlogin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            data = request.json
            required = ['fullname', 'email', 'phone', 'password']
            if not all(data.get(field) for field in required):
                return jsonify({'success': False, 'message': 'All fields are required'})
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (fullname, email, phone, password) VALUES (%s, %s, %s, %s)",
                           (data['fullname'], data['email'], data['phone'], data['password']))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except mysql.connector.Error as err:
            if 'Duplicate' in str(err):
                return jsonify({'success': False, 'message': 'Email already exists'})
            return jsonify({'success': False, 'message': 'Database Error'})
        except Exception as e:
            logger.error(f"Signup Error: {e}")
            return jsonify({'success': False, 'message': 'Server Error'})
    return render_template('user/usersignup.html')

@app.route('/logout')
def logout(): 
    session.clear()
    return redirect('/')

# --- USER ---
@app.route('/predict')
def predict_page(): 
    return render_template('user/predict.html') if 'user_id' in session else redirect('/login')

@app.route('/detect', methods=['POST'])
def detect():
    if 'user_id' not in session: 
        return jsonify({'error': 'Auth required'}), 401
    
    file = request.files.get('plant-image')
    if not file:
        return jsonify({'error': 'No file provided'})
    
    try:
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'})
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result = analyze_plant_health(filepath)
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO predictions (user_id, image_path, plant_type, disease_name, status, severity_score) VALUES (%s, %s, %s, %s, %s, %s)",
                        (session['user_id'], f"uploads/{filename}", request.form.get('plant-type', 'Unknown'), 
                         result['disease_name'], result['status'], result['confidence']))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error during prediction save: {e}")
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': 'Processing failed'}), 500


@app.route('/history')
def history():
    try:
        if 'user_id' not in session: 
            return redirect('/login')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM predictions WHERE user_id=%s ORDER BY created_at DESC", (session.get('user_id'),))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('user/result.html', history=data)
    except Exception as e:
        logger.error(f"History error: {e}")
        return render_template('user/result.html', history=[])

@app.route('/alerts')
def alerts():
    try:
        if 'user_id' not in session:
            return redirect('/login')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Get alerts specific to this user
        cursor.execute("""
            SELECT a.*, ua.id as user_alert_id, ua.is_read 
            FROM alerts a
            LEFT JOIN user_alerts ua ON a.id = ua.alert_id AND ua.user_id=%s
            ORDER BY a.created_at DESC LIMIT 20
        """, (session['user_id'],))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('user/useralerts.html', alerts=data)
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return render_template('user/useralerts.html', alerts=[])

@app.route('/notifications')
def notifications():
    """Get user notifications"""
    try:
        if 'user_id' not in session:
            return redirect('/login')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_id=%s 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (session['user_id'],))
        notifs = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('user/notifications.html', notifications=notifs)
    except Exception as e:
        logger.error(f"Notifications error: {e}")
        return render_template('user/notifications.html', notifications=[])

@app.route('/api/notifications/unread')
def get_unread_notifications():
    """Get count of unread notifications"""
    try:
        if 'user_id' not in session:
            return jsonify({'count': 0}), 401
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM notifications WHERE user_id=%s AND is_read=FALSE",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'count': result[0]})
    except Exception as e:
        logger.error(f"Unread notifications error: {e}")
        return jsonify({'count': 0}), 500

@app.route('/api/notification/<int:notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False}), 401
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read=TRUE, read_at=NOW() WHERE id=%s AND user_id=%s",
            (notif_id, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/notifications/list')
def get_notifications_api():
    """Get notifications via API"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'notifications': []}), 401
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notifications 
            WHERE user_id=%s 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (session['user_id'],))
        notifs = cursor.fetchall()
        
        # Convert datetime objects to ISO format strings for JavaScript
        for notif in notifs:
            if notif.get('created_at'):
                notif['created_at'] = notif['created_at'].isoformat()
            if notif.get('read_at'):
                notif['read_at'] = notif['read_at'].isoformat()
        
        cursor.close()
        conn.close()
        logger.info(f"Returning {len(notifs)} notifications for user {session['user_id']}")
        return jsonify({'success': True, 'notifications': notifs})
    except Exception as e:
        logger.error(f"Get notifications API error: {e}")
        return jsonify({'success': False, 'notifications': []}), 500

@app.route('/api/notifications/permission', methods=['POST'])
def save_notification_permission():
    """Save user's browser notification permission status"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False}), 401
        logger.info(f"User {session['user_id']} enabled browser notifications")
        return jsonify({'success': True, 'message': 'Notifications enabled'})
    except Exception as e:
        logger.error(f"Permission error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/test-notification', methods=['POST'])
def test_notification():
    """Test endpoint to create a test notification"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, is_read)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (session['user_id'], 'test', 'Test Notification', 'This is a test notification to verify the system is working.'))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Test notification created for user {session['user_id']}")
        return jsonify({'success': True, 'message': 'Test notification created'})
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            data = request.json
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Not authenticated'})
            
            # You can save complaints to a table if needed
            logger.info(f"Complaint from user {session['user_id']}: {data.get('message')}")
            return jsonify({'success': True, 'message': 'Thank you for your complaint'})
        except Exception as e:
            logger.error(f"Complaint error: {e}")
            return jsonify({'success': False, 'message': 'Error submitting complaint'})
    return render_template('user/complaint.html')

# --- ADMIN ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            data = request.json
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role='admin'", 
                          (data['email'], data['password']))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['role'] = 'admin'
                session['fullname'] = user['fullname']
                return jsonify({'success': True, 'redirect': '/admin/dashboard'})
            return jsonify({'success': False, 'message': 'Invalid admin credentials'})
        except Exception as e:
            logger.error(f"Admin login error: {e}")
            return jsonify({'success': False, 'message': 'Server Error'})
    return render_template('admin/adminlogin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': 
        return redirect('/admin/login')
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as c FROM users WHERE role='user'")
        u = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM predictions")
        r = cursor.fetchone()['c']
        cursor.execute("SELECT COUNT(*) as c FROM alerts")
        a = cursor.fetchone()['c']
        
        # Get recent activity
        cursor.execute("""
            SELECT p.*, u.fullname, u.email 
            FROM predictions p 
            JOIN users u ON p.user_id=u.id 
            ORDER BY p.created_at DESC 
            LIMIT 5
        """)
        act = cursor.fetchall()
        
        # NEW CODE: Fetch Critical Cases for Admin Visibility
        cursor.execute("""
            SELECT p.*, u.fullname, u.email 
            FROM predictions p 
            JOIN users u ON p.user_id=u.id 
            WHERE p.status = 'Critical'
            ORDER BY p.created_at DESC 
            LIMIT 5
        """)
        critical_cases = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('admin/dashboard.html', 
                             user_count=u, 
                             report_count=r, 
                             alert_count=a, 
                             activities=act, 
                             critical_cases=critical_cases) # Passed new data
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return f"Database Error: {e}"

@app.route('/admin/history')
def admin_history():
    if session.get('role') != 'admin': 
        return redirect('/admin/login')
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.fullname FROM predictions p JOIN users u ON p.user_id=u.id ORDER BY p.created_at DESC")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin/history.html', history=data)
    except Exception as e:
        logger.error(f"Admin history error: {e}")
        return f"Error: {e}"

@app.route('/admin/alerts', methods=['GET', 'POST'])
def admin_alerts():
    if session.get('role') != 'admin': 
        return redirect('/admin/login')
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        data = cursor.fetchall()
        
        # Fetch users for dropdown
        cursor.execute("SELECT id, fullname, email FROM users WHERE role='user' ORDER BY fullname")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('admin/alert.html', alert_history=data, users=users)
    except Exception as e:
        logger.error(f"Admin alerts error: {e}")
        return "DB Error"

@app.route('/admin/send_alert', methods=['POST'])
def send_alert():
    if session.get('role') != 'admin': 
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        d = request.json
        if not d.get('priority') or not d.get('disease') or not d.get('region') or not d.get('message'):
            return jsonify({'success': False, 'message': 'All fields required'})
        
        target_users = d.get('target_users', 'all')  # 'all' or comma-separated user IDs
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Insert alert into alerts table
        cursor.execute("INSERT INTO alerts (priority, disease_name, region, message) VALUES (%s, %s, %s, %s)",
                    (d['priority'], d['disease'], d['region'], d['message']))
        conn.commit()
        alert_id = cursor.lastrowid
        logger.info(f"Alert created with ID: {alert_id}")
        
        # Determine target users
        user_ids = []
        user_emails = []
        
        # NEW CODE: Logic for Specific Email vs All Users
        if '@' in target_users:
            # Case 1: Specific Gmail/Email Address
            user_emails = [target_users.strip()]
            # We don't link to a user ID for guest emails, or we could lookup if it exists
            # For simplicity, we just send the email.
            logger.info(f"Targeting specific email: {user_emails}")
        
        elif target_users.lower() == 'all':
            # Case 2: All Registered Users
            cursor.execute("SELECT id, email FROM users WHERE role='user'")
            users = cursor.fetchall()
            user_ids = [u[0] for u in users]
            user_emails = [u[1] for u in users if u[1]]
            logger.info(f"Target users: {user_ids}")
            
        else:
            # Case 3: Specific User IDs (Existing logic)
            try:
                raw_ids = [int(uid.strip()) for uid in target_users.split(',') if uid.strip()]
                if raw_ids:
                    # Fetch valid users and their emails
                    placeholders = ','.join(['%s'] * len(raw_ids))
                    cursor.execute(f"SELECT id, email FROM users WHERE id IN ({placeholders})", tuple(raw_ids))
                    users = cursor.fetchall()
                    user_ids = [u[0] for u in users]
                    user_emails = [u[1] for u in users if u[1]]
            except ValueError:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid user IDs'})
                
        # Send Email Alert
        if user_emails:
            try:
                from email_utils import send_alert_email
                send_alert_email(
                    app, 
                    f"Plant Health Alert: {d['disease']}", 
                    user_emails, 
                    'email/alert_email.html',
                    region=d['region'],
                    disease=d['disease'],
                    priority=d['priority'],
                    message=d['message'],
                    year=datetime.now().year
                )
            except Exception as e:
                logger.error(f"Failed to initiate email sending: {e}")
        
        # Create user_alerts entries and notifications
        notification_count = 0
        for uid in user_ids:
            try:
                cursor.execute("""
                    INSERT INTO user_alerts (user_id, alert_id, is_read, notified_at)
                    VALUES (%s, %s, FALSE, NOW())
                    ON DUPLICATE KEY UPDATE is_read=FALSE
                """, (uid, alert_id))
                
                cursor.execute("""
                    INSERT INTO notifications (user_id, type, title, message, related_alert_id, is_read)
                    VALUES (%s, %s, %s, %s, %s, FALSE)
                """, (uid, 'alert', f'Alert: {d["disease"]}', d['message'], alert_id))
                notification_count += 1
            except Exception as e:
                logger.error(f"Error creating notification for user {uid}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Alert sent successfully. Created {notification_count} notifications for {len(user_ids)} users: {d['disease']} in {d['region']}")
        return jsonify({'success': True, 'message': f'Alert sent to {len(user_ids)} user(s)'})
    except Exception as e:
        logger.error(f"Send alert error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/broadcast', methods=['POST'])
def send_broadcast():
    """
    # NEW CODE: Admin Awareness Broadcast
    Sends a general email to all users or specific targets.
    """
    if session.get('role') != 'admin': 
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    try:
        data = request.json
        subject = data.get('subject', 'Plant Health Awareness')
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'message': 'Content is required'})

        conn = get_db()
        cursor = conn.cursor()
        
        # Reuse logic: Fetch all user emails
        # For broadcast, default is usually ALL
        cursor.execute("SELECT email FROM users WHERE role='user'")
        users = cursor.fetchall()
        user_emails = [u[0] for u in users if u[0]]
        
        cursor.close()
        conn.close()
        
        # Send Email using the new helper
        if user_emails:
            from email_utils import send_general_email
            send_general_email(app, subject, user_emails, content)
            
        return jsonify({'success': True, 'message': f'Broadcast sent to {len(user_emails)} users'})
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__': 
    app.run(debug=True)