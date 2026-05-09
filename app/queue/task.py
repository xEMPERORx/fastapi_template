import asyncio
from app.queue.celery import app
from app.services.verify import mail_config
from app.services.verify.mail_config import create_message

@app.task(name="send_email_bg")
def send_email_bg(recipients: list[str], subject: str, body: str):
    message = create_message(recipients=recipients, subject=subject, body=body)
    async def _send():
        await mail_config.mail.send_message(message)
    try:
        asyncio.run(_send())
        print(f"Email sent to {recipients}")
    except Exception as e:
        print(f"Failed to send email: {e}")

