import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTransportError(Exception):
    """Base exception for email transport failures."""
    pass


class TransientEmailError(EmailTransportError):
    """Temporary errors (timeouts, rate limits, server busy) that should be retried."""
    pass


class PermanentEmailError(EmailTransportError):
    """Permanent errors (mailbox not found, rejected syntax) that should not be retried."""
    pass


class EmailSenderService:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        mock_mode: bool = False,
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.username = username if username is not None else settings.SMTP_USER
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_TLS
        self.use_ssl = use_ssl if use_ssl is not None else settings.SMTP_SSL
        self.from_email = from_email or settings.EMAILS_FROM_EMAIL
        self.from_name = from_name or settings.EMAILS_FROM_NAME
        self.mock_mode = mock_mode

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        unsubscribe_url: Optional[str] = None,
    ) -> str:
        """
        Sends an email message via SMTP.
        Returns the generated Message-ID on success.
        Raises TransientEmailError or PermanentEmailError on failure.
        """
        if self.mock_mode or settings.ENVIRONMENT == "test_mock":
            message_id = make_msgid(domain="mock.local")
            logger.info(f"[MOCK EMAIL] Sent to={to_email}, subject='{subject}', msg_id={message_id}")
            return message_id

        msg = MIMEMultipart("alternative")
        from_header = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["From"] = from_header
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        message_id = make_msgid()
        msg["Message-ID"] = message_id
        msg["Precedence"] = "bulk"

        if unsubscribe_url:
            msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
            msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        # Plain text fallback
        if text_content:
            part_text = MIMEText(text_content, "plain", "utf-8")
            msg.attach(part_text)
        else:
            # Simple text strip
            plain = html_content.replace("<br>", "\n").replace("<br/>", "\n").replace("</p>", "\n\n")
            # Remove remaining tags simply
            import re
            plain = re.sub(r"<[^>]+>", "", plain).strip()
            msg.attach(MIMEText(plain, "plain", "utf-8"))

        # HTML part
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_html)

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=15)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=15)

            with server:
                if self.use_tls and not self.use_ssl:
                    server.starttls(context=ssl.create_default_context())
                if self.username and self.password:
                    server.login(self.username, self.password)
                
                server.send_message(msg)
                logger.info(f"Successfully sent email to {to_email} with Message-ID {message_id}")
                return message_id

        except smtplib.SMTPRecipientsRefused as e:
            logger.warning(f"Permanent rejection for recipient {to_email}: {e}")
            raise PermanentEmailError(f"Recipient refused: {e}")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication error: {e}")
            raise PermanentEmailError(f"SMTP Auth error: {e}")
        except (
            smtplib.SMTPConnectError,
            smtplib.SMTPServerDisconnected,
            smtplib.SMTPResponseException,
            TimeoutError,
            ConnectionRefusedError,
            OSError,
        ) as e:
            # Check for transient vs permanent response code
            if isinstance(e, smtplib.SMTPResponseException):
                code = e.smtp_code
                if 400 <= code < 500:
                    raise TransientEmailError(f"Temporary SMTP error {code}: {e.smtp_error.decode(errors='ignore')}")
                else:
                    raise PermanentEmailError(f"Permanent SMTP error {code}: {e.smtp_error.decode(errors='ignore')}")
            logger.warning(f"Transient network/SMTP error sending to {to_email}: {e}")
            raise TransientEmailError(f"Network/SMTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}", exc_info=True)
            raise TransientEmailError(f"Unexpected error: {str(e)}")


email_sender = EmailSenderService()
