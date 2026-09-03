import smtplib
import ssl
from email.message import EmailMessage
import config_manager
import contact_manager # <--- NEW

def send_email_direct(recipient_email, body):
    # 1. CHECK CONFIG
    cfg = config_manager.load_config()
    sender_email = cfg.get("email")
    app_password = cfg.get("password")

    if not sender_email or not app_password:
        return "NO_CONFIG"

    # 2. SEND
    em = EmailMessage()
    em['From'] = sender_email
    em['To'] = recipient_email
    em['Subject'] = "Message from Cosmo AI"
    em.set_content(body)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender_email, app_password)
            smtp.sendmail(sender_email, recipient_email, em.as_string())
        return "SUCCESS"
    except Exception as e:
        print(f"Email Error: {e}")
        return "FAIL"