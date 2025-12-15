"""Email service using Aliyun DirectMail via SMTP."""

from __future__ import annotations

import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from jinja2 import Template

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service backed by Aliyun DirectMail SMTP."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        self.frontend_url = settings.frontend_url
        self.smtp_host = "smtpdm.aliyun.com"
        self.smtp_port = 465
        self.smtp_password = settings.aliyun_smtp_password or settings.aliyun_access_key_secret

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email via Aliyun DirectMail SMTP."""

        def _send() -> bool:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg.set_content(text_content or "This email requires an HTML-capable client.")
            msg.add_alternative(html_content, subtype="html")

            context = ssl.create_default_context()
            try:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.from_email, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            except Exception as e:
                logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
                return False

        return await asyncio.to_thread(_send)

    async def send_verification_code(
        self,
        to_email: str,
        code: str,
        username: Optional[str] = None,
    ) -> bool:
        """Send verification code email."""
        subject = "验证您的邮箱 - 工业问答系统"
        html_template = """
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>{% if username %}亲爱的 {{ username }}，{% else %}您好，{% endif %}</p>
                <p>您的邮箱验证码是：</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="display: inline-block; padding: 15px 30px; background: #1677ff; color: #fff; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 4px;">{{ code }}</span>
                </div>
                <p>验证码5分钟内有效，请勿泄露给他人。</p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">如果这不是您的操作，请忽略此邮件。</p>
            </div>
        </body>
        </html>
        """
        html = Template(html_template).render(
            username=username,
            code=code,
        )
        # 纯文本版本
        text_content = f"您的邮箱验证码是：{code}，验证码5分钟内有效。"
        return await self.send_email(to_email=to_email, subject=subject, html_content=html, text_content=text_content)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        username: Optional[str] = None,
    ) -> bool:
        """Send password reset email."""
        subject = "重置您的密码 - 工业问答系统"
        html_template = """
        <!DOCTYPE html>
        <html>
        <body>
            <p>{% if username %}亲爱的 {{ username }}，{% else %}您好，{% endif %}</p>
            <p>请点击下面的按钮重置密码：</p>
            <p><a href="{{ reset_url }}" style="padding:10px 16px;background:#d4380d;color:#fff;text-decoration:none;border-radius:4px;">重置密码</a></p>
            <p>或复制链接到浏览器： {{ reset_url }}</p>
            <p>链接1小时内有效。</p>
        </body>
        </html>
        """
        html = Template(html_template).render(
            username=username,
            reset_url=reset_url,
        )
        return await self.send_email(to_email=to_email, subject=subject, html_content=html)



