"""
Mock email service — saves .eml file, no external calls.
"""
from pathlib import Path
from uuid import uuid4

import structlog

log = structlog.get_logger()

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def mock_send_email(to: str, subject: str, body: str, run_id: str) -> dict:
    state_dir = WORKSPACE / ".state" / run_id
    state_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise filename
    safe_to = to.replace("@", "_at_").replace(".", "_")
    eml_path = state_dir / f"email_{safe_to}.eml"
    eml_path.write_text(
        f"To: {to}\nSubject: {subject}\n\n{body}",
        encoding="utf-8",
    )
    msg_id = f"mock-{uuid4().hex[:8]}"
    log.info("mock_email_sent", to=to, subject=subject, message_id=msg_id, run_id=run_id)
    return {"status": "sent", "message_id": msg_id}
