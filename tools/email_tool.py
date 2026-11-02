import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_email(job_report: str) -> bool:
    """Send the daily job report email. Returns True on success."""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    if not all([email_user, email_password, recipient_email]):
        print("Error: Email credentials are not fully configured in .env")
        return False

    subject = f"Daily Software Engineering Jobs - {datetime.now().strftime('%d/%m/%Y')}"
    body = f"""Good Morning Fabian,

Here are today's Software Engineering jobs.

{job_report}

Have a productive day.
"""
    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(email_user, email_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: [{type(e).__name__}] {e}")
        return False
