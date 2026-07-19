import asyncio
from datetime import datetime

from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import async_sessionmaker

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


@app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Periodic housekeeping: refresh tokens accumulate forever otherwise."""
    from app.database.postgres_db import engine
    from app.models.db_model import RefreshToken

    async def _cleanup() -> int:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            result = await session.execute(
                delete(RefreshToken).where(
                    or_(RefreshToken.expires_at < datetime.utcnow(), RefreshToken.is_revoked.is_(True))
                )
            )
            await session.commit()
            return result.rowcount or 0

    try:
        deleted = asyncio.run(_cleanup())
        print(f"cleanup_expired_tokens: removed {deleted} refresh token rows")
    except Exception as e:
        print(f"cleanup_expired_tokens failed: {e}")

