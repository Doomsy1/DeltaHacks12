"""
Browser session store for pending verification sessions.

Keeps browser pages alive in memory while waiting for user to provide
email verification codes via the API.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from playwright.async_api import Page, Browser, BrowserContext

# Session timeout (15 minutes)
SESSION_TIMEOUT_SECONDS = 900

# In-memory store for pending sessions
_pending_sessions: dict[str, "PendingSession"] = {}
_cleanup_task: asyncio.Task | None = None


@dataclass
class PendingSession:
    """A browser session waiting for verification code."""
    application_id: str
    page: Page
    browser: Browser
    context: BrowserContext
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if this session has expired."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=SESSION_TIMEOUT_SECONDS)


def store_session(
    application_id: str,
    page: Page,
    browser: Browser,
    context: BrowserContext
) -> None:
    """
    Store a browser session for later verification.
    
    Args:
        application_id: The application ID this session belongs to
        page: The Playwright page with verification modal open
        browser: The browser instance
        context: The browser context
    """
    global _cleanup_task
    
    # Remove any existing session for this app
    if application_id in _pending_sessions:
        asyncio.create_task(_close_session(application_id))
    
    _pending_sessions[application_id] = PendingSession(
        application_id=application_id,
        page=page,
        browser=browser,
        context=context
    )
    
    print(f"Stored verification session for {application_id} (timeout: {SESSION_TIMEOUT_SECONDS}s)")
    
    # Start cleanup task if not running
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_expired_sessions())


def get_session(application_id: str) -> PendingSession | None:
    """
    Get a pending session by application ID.
    
    Returns None if session doesn't exist or is expired.
    """
    session = _pending_sessions.get(application_id)
    
    if session is None:
        return None
    
    if session.is_expired():
        # Clean up expired session
        asyncio.create_task(_close_session(application_id))
        return None
    
    return session


async def remove_session(application_id: str) -> None:
    """Remove and close a session."""
    await _close_session(application_id)


async def _close_session(application_id: str) -> None:
    """Close browser and remove session from store."""
    session = _pending_sessions.pop(application_id, None)
    if session:
        try:
            await session.browser.close()
            print(f"Closed verification session for {application_id}")
        except Exception as e:
            print(f"Error closing session {application_id}: {e}")


async def _cleanup_expired_sessions() -> None:
    """Background task to clean up expired sessions."""
    while _pending_sessions:
        await asyncio.sleep(60)  # Check every minute
        
        expired = [
            app_id for app_id, session in _pending_sessions.items()
            if session.is_expired()
        ]
        
        for app_id in expired:
            print(f"Session {app_id} expired, cleaning up...")
            await _close_session(app_id)
    
    print("No more pending sessions, cleanup task exiting")


def get_session_count() -> int:
    """Get the number of active sessions."""
    return len(_pending_sessions)


def get_session_info(application_id: str) -> dict[str, Any] | None:
    """Get info about a session without returning the actual objects."""
    session = _pending_sessions.get(application_id)
    if session is None:
        return None
    
    remaining = (session.created_at + timedelta(seconds=SESSION_TIMEOUT_SECONDS)) - datetime.utcnow()
    
    return {
        "application_id": application_id,
        "created_at": session.created_at.isoformat(),
        "expires_in_seconds": max(0, int(remaining.total_seconds())),
        "is_expired": session.is_expired()
    }
