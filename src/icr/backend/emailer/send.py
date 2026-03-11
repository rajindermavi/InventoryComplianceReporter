"""Email dispatch via nicemail MS Graph backend."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from icr.backend.emailer.draft import DraftingResult


@dataclass(frozen=True)
class SendResult:
    """Result of a dispatch operation."""

    sent: int
    failed: int
    errors: tuple[str, ...]


def send_drafts(
    drafts: DraftingResult,
    *,
    from_email: str,
    client_id: str,
    backend: str = "ms_graph",
    authority: str = "organization",
    client_secret: str | None = None,
    passphrase: str | None = None,
    show_message: Callable[[Any], None] | None = None,
) -> SendResult:
    """Send drafted emails via nicemail.

    Args:
        drafts: DraftingResult from draft_emails().
        from_email: Sender email address.
        client_id: OAuth app client ID.
        backend: nicemail backend ('ms_graph' or 'google_api').
        authority: MSAL authority type ('organization', 'common', 'consumer'). MS Graph only.
        client_secret: OAuth client secret. Google API only.
        passphrase: Optional nicemail passphrase for credential storage.
        show_message: Callback for device code flow messages.
    """
    from nicemail import EmailClient

    if backend == "google_api":
        client = EmailClient(
            backend="google_api",
            google_api_config={
                "email_address": from_email,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            passphrase=passphrase,
        )
    else:
        client = EmailClient(
            backend="ms_graph",
            msal_config={
                "email_address": from_email,
                "client_id": client_id,
                "authority": authority,
            },
            passphrase=passphrase,
        )

    sent = 0
    failed = 0
    errors: list[str] = []

    all_drafts = list(drafts.drafts)
    if not all_drafts:
        return SendResult(sent=0, failed=0, errors=())

    def _build_kwargs(draft: Any) -> dict[str, Any]:
        attachment_paths = [
            str(att.path)
            for att in draft.attachments
            if att.path is not None and att.path.exists()
        ]
        kwargs: dict[str, Any] = {
            "to": list(draft.to_addresses),
            "subject": draft.subject,
            "body_html": draft.html_body,
            "from_address": from_email,
        }
        if attachment_paths:
            kwargs["attachments"] = attachment_paths
        if show_message is not None:
            kwargs["show_message"] = show_message
        return kwargs

    # First send is outside the error-collection loop so that auth failures
    # raise immediately rather than being silently counted as a vessel failure.
    first, *rest = all_drafts
    try:
        client.send(**_build_kwargs(first))
        sent += 1
    except Exception as exc:
        raise RuntimeError(f"Email dispatch failed (authentication or connection error): {exc}") from exc

    for draft in rest:
        try:
            client.send(**_build_kwargs(draft))
            sent += 1
        except Exception as exc:
            failed += 1
            errors.append(f"{draft.vessel_id}: {exc}")

    return SendResult(sent=sent, failed=failed, errors=tuple(errors))
