import os
import logging
from typing import Optional, Dict, Any, List

from pywebpush import webpush, WebPushException


VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:admin@antitheft.com")

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")


def _can_send() -> bool:
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY and VAPID_SUBJECT)


def send_push_notifications(
    subscriptions: List[Dict[str, Any]],
    title: str,
    body: str,
    url: Optional[str] = None,
    icon: Optional[str] = None,
) -> Dict[str, int]:
    """
    Send a Web Push notification to all subscriptions.
    subscriptions items must be in pywebpush format:
      {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}
    """
    if not _can_send():
        logging.warning("[PUSH] VAPID keys not configured; skipping push notifications")
        return {"sent": 0, "failed": 0}

    payload: Dict[str, Any] = {"title": title, "body": body}
    if url:
        payload["url"] = url
    if icon:
        payload["icon"] = icon

    sent = 0
    failed = 0

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub,
                data=json_dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_SUBJECT},
            )
            sent += 1
        except WebPushException as e:
            failed += 1
            logging.warning(f"[PUSH] Failed to send push: {e}")
        except Exception as e:
            failed += 1
            logging.warning(f"[PUSH] Unexpected error sending push: {e}")

    return {"sent": sent, "failed": failed}


def json_dumps(obj: Dict[str, Any]) -> str:
    # tiny helper to avoid importing json everywhere
    import json
    return json.dumps(obj)

