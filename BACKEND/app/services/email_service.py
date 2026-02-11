# app/services/email_service.py
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.models.models import OutboundMessage, User, UserEngagementEvent
from app.enums.db_enums import DeliveryChannelEnum, EngagementStateEnum
from app.enums.db_enums import EntityTypeEnum



# Configure Logging
logger = logging.getLogger(__name__)

# Try importing Resend (Handle ImportError if not installed)
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

def _send_smtp(to_email: str, subject: str, html_content: str):
    """
    Fallback SMTP sender using Gmail or standard SMTP.
    """
    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USERNAME")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return "sent_via_smtp"
    except Exception as e:
        logger.error(f"SMTP Failed: {e}")
        return f"failed_smtp: {str(e)}"

def send_email_notification(to_email: str, subject: str, html_content: str):
    """
    Primary Email Sender: Resend -> SMTP Fallback
    """
    # 1. Try Resend
    if RESEND_AVAILABLE and os.getenv("RESEND_API_KEY"):
        try:
            resend.api_key = os.getenv("RESEND_API_KEY")
            from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev") # Verify this domain in Resend
            
            resend.Emails.send({
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            })
            return "sent_via_resend"
        except Exception as e:
            logger.warning(f"Resend API failed, switching to SMTP: {e}")

    # 2. Fallback to SMTP
    return _send_smtp(to_email, subject, html_content)

def send_email_and_log(
    db: Session,
    user_id: str,
    session_id: str,
    subject: str,
    html_content: str,
    message_type: str, # 'order_confirmation', 'otp', 'offer'
):
    """
    Sends email and logs to DB for Agent Observability.
    """
    user = db.query(User).get(user_id)
    if not user or not user.email:
        return None

    # 1. Create Engagement Event (Intent to send)
    engagement = UserEngagementEvent(
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.user_session, # Generic entity
        entity_id=session_id,
        channel=DeliveryChannelEnum.email,
        state=EngagementStateEnum.sent,
        event_metadata_data={"subject": subject, "message_type": message_type}
    )
    db.add(engagement)
    db.flush()

    # 2. Send
    status = send_email_notification(user.email, subject, html_content)
    
    final_status = "sent" if "sent" in status else "failed"

    # 3. Log Outbound Message
    outbound = OutboundMessage(
        user_id=user_id,
        session_id=session_id,
        channel=DeliveryChannelEnum.email,
        engagement_event_id=engagement.id,
        message_type=message_type,
        content=html_content[:1000], # Store preview only to save space
        status=final_status
    )
    db.add(outbound)
    db.commit()
    return outbound