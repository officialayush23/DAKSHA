# app/services/email_service.py

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

# 👇 NEW: Import your centralized settings to reliably read the .env file
from app.core.config import settings

from app.models.models import OutboundMessage, User, UserEngagementEvent
from app.enums.db_enums import DeliveryChannelEnum, EngagementStateEnum, EntityTypeEnum

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

def _send_smtp(to_email: str, subject: str, html_content: str) -> bool:
    # 🛡️ SAFETY CHECK: Ensure recipient email exists
    if not to_email:
        return False
        
    try:
        # 👇 FIXED: Use the Pydantic settings object instead of os.getenv()
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME
        smtp_pass = settings.SMTP_PASSWORD
        from_email = settings.SMTP_FROM_EMAIL

        # 🛡️ NEW SAFETY CHECK: Catch missing credentials gracefully
        if not smtp_user or not smtp_pass:
            logger.error("SMTP Configuration missing. Please check SMTP_USERNAME and SMTP_PASSWORD in your .env")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        
        # Will no longer crash with 'NoneType has no attribute encode'
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
    session_id=None,
    subject: str,
    html_content: str,
    message_type: str,
    source: str = "system",
    entity_id=None,
    entity_type: EntityTypeEnum = EntityTypeEnum.user_session
):
    user = db.get(User, user_id)
    
    # 🛡️ SAFETY CHECK: Abort entirely if the user has no email address.
    if not user or not user.email:
        logger.info(f"Skipping email for user {user_id}: No email address on file.")
        return None

    # 🛡️ SAFETY CHECK: Ensure we always have a valid UUID for the database
    safe_entity_id = entity_id or session_id or user_id

    engagement = UserEngagementEvent(
        user_id=user_id,
        session_id=session_id,
        entity_type=entity_type,
        entity_id=safe_entity_id,
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

    # Try Resend first, fallback to standard SMTP (Gmail)
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