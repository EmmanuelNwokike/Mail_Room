import os
# email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    """
    Simple email service for sending package notification emails
    to residents when a package is delivered.
    """

    def __init__(self):
        # These are based on the sample provided in your assignment.
        # If these credentials change or stop working, your professor
        # will usually let you know.
        self.smtp_host = "mail.privateemail.com"
        self.smtp_port = 587
        self.sender_email = "noreply@buffteks.org"
        self.password = os.environ.get("MAILROOM_SMTP_PASSWORD", "")

    def send_package_notification(self, to_email: str, resident_name: str):
        """
        Send a 'package received' email to the resident.
        """
        subject = "Package Pickup Notification"

        # HTML body (you can tweak wording if you like)
        html_content = f"""
        <html>
            <body>
                <p>Dear {resident_name},</p>
                <p>We have received a package for you at the leasing office. Due to limited storage space, 
                please pick up your package within <strong>5 days</strong>.</p>
                <p>If the package is not picked up within this time frame, it will be returned to the post office.</p>
                <p>Thank you!</p>
                <p>BuffTeks Apartment Leasing Office</p>
            </body>
        </html>
        """

        # Build message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.sender_email
        message['To'] = to_email

        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Connect and send
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(message)

            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
