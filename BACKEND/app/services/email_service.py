# app/services/email_service.py
# app/services/email_service.py

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.models.models import OutboundMessage, User, UserEngagementEvent
from app.enums.db_enums import DeliveryChannelEnum, EngagementStateEnum, EntityTypeEnum

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

def _send_smtp(to_email: str, subject: str, html_content: str) -> bool:
    # 🛡️ SAFETY CHECK: Ensure email exists
    if not to_email:
        return False
        
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
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False

def _send_resend(to_email: str, subject: str, html_content: str) -> bool:
    if not RESEND_AVAILABLE or not os.getenv("RESEND_API_KEY") or not to_email:
        return False

    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        resend.Emails.send({
            "from": os.getenv("EMAIL_FROM", "onboarding@resend.dev"),
            "to": to_email,
            "subject": subject,
            "html": html_content,
        })
        return True
    except Exception as e:
        logger.warning(f"Resend failed: {e}")
        return False

def send_email_and_log(
    db: Session,
    *,
    user_id,
    session_id,
    subject: str,
    html_content: str,
    message_type: str,
    source: str = "system", 
):
    user = db.get(User, user_id)
    
    # 🛡️ SAFETY CHECK: Abort entirely if the user has no email address.
    if not user or not user.email:
        logger.info(f"Skipping email for user {user_id}: No email address on file.")
        return None

    engagement = UserEngagementEvent(
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.user_session,
        entity_id=session_id,
        channel=DeliveryChannelEnum.email,
        state=EngagementStateEnum.pending,
        event_metadata_data={
            "subject": subject,
            "message_type": message_type,
            "source": source,
        },
    )
    db.add(engagement)
    db.flush()

    sent = _send_resend(user.email, subject, html_content)
    if not sent:
        sent = _send_smtp(user.email, subject, html_content)

    engagement.state = EngagementStateEnum.sent if sent else EngagementStateEnum.failed

    outbound = OutboundMessage(
        user_id=user_id,
        session_id=session_id,
        channel=DeliveryChannelEnum.email,
        engagement_event_id=engagement.id,
        message_type=message_type,
        content=html_content[:1000],
        status="sent" if sent else "failed",
    )
    db.add(outbound)
    db.commit()

    return outbound