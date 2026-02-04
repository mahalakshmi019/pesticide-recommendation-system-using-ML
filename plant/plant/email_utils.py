import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from flask import render_template, current_app

def send_async_email(app, msg):
    with app.app_context():
        try:
            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            app.logger.info(f"Email sent successfully to {msg['Bcc']}")
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")

def send_alert_email(app, subject, recipients, template, **kwargs):
    """
    Send an email to multiple recipients using a template.
    """
    if not recipients:
        return

    msg = MIMEMultipart()
    sender = kwargs.get('sender', app.config.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME']))
    msg['From'] = sender
    msg['To'] = app.config['MAIL_USERNAME']  # Primary TO is sender to hide recipients
    msg['Bcc'] = ", ".join(recipients)
    msg['Subject'] = subject

    # Render HTML body
    # Using app.app_context() is tricky inside a thread if we pass 'app' 
    # but to render_template we need context.
    # Preferably render before threading.
    
    with app.app_context():
        html_body = render_template(template, **kwargs)

    msg.attach(MIMEText(html_body, 'html'))

    # Start thread
    # We pass the app instance (or rely on passed config). 
    # Passing the app instance to a thread can be unsafe if contexts are popping.
    # But usually okay for simple config access if careful. 
    # Better to extract config? 
    # For now, following the pattern of passing app to maintain context for extensions if needed,
    # but simpler to just run the SMTP part in thread.
    
    real_app = app._get_current_object() if hasattr(app, '_get_current_object') else app
    thr = threading.Thread(target=send_async_email, args=(real_app, msg))
    thr.start()

def send_general_email(app, subject, recipients, body_content, **kwargs):
    """
    Send a general email to multiple recipients (Admin Broadcast).
    """
    if not recipients:
        return

    msg = MIMEMultipart()
    sender = kwargs.get('sender', app.config.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME']))
    msg['From'] = sender
    msg['To'] = app.config['MAIL_USERNAME']  # Hide recipients
    msg['Bcc'] = ", ".join(recipients)
    msg['Subject'] = subject

    # Simple HTML wrapper
    html_body = f"""
    <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #333; line-height: 1.6;">
            <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; border: 1px solid #e9ecef;">
                <h2 style="color: #2c3e50; margin-top: 0;">{subject}</h2>
                <div style="margin-top: 20px; font-size: 16px;">
                    {body_content}
                </div>
                <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #777; margin-bottom: 0;">Sent from PlantGuard Admin System</p>
            </div>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, 'html'))
    
    real_app = app._get_current_object() if hasattr(app, '_get_current_object') else app
    thr = threading.Thread(target=send_async_email, args=(real_app, msg))
    thr.start()
