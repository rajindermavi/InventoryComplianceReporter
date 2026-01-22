"""Phase 7B email delivery orchestrator.

Consumes existing .eml draft artifacts and dispatches them via configured
transports without inspecting or modifying content.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Protocol

from .models import EmailDeliveryPlan, EmailDeliveryResult
from .transports import EmailTransport, SmtpConfig, SmtpTransport, TransportResult


class _LoggerLike(Protocol):
    def info(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def warning(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def error(self, msg: str, *args: object, **kwargs: object) -> None: ...

    def exception(self, msg: str, *args: object, **kwargs: object) -> None: ...


@dataclass(frozen=True)
class _ResolvedTransport:
    transport: EmailTransport | None
    name: str | None
    reason: str | None


def deliver_emails(
    run_paths: object,
    vessels: Iterable[object],
    delivery_plan: EmailDeliveryPlan | Mapping[str, object] | object,
    logger: _LoggerLike | None,
) -> list[EmailDeliveryResult]:
    """Send existing .eml drafts via the configured transport."""

    send_now = bool(_get_option(delivery_plan, "send_now", False))
    confirm_send = bool(_get_option(delivery_plan, "confirm_send", False))

    if not send_now:
        return _skip_all(
            vessels,
            reason="Email delivery disabled by user.",
            transport=_get_option(delivery_plan, "transport", None),
        )
    if send_now and not confirm_send:
        return _skip_all(
            vessels,
            reason="Email delivery not confirmed.",
            transport=_get_option(delivery_plan, "transport", None),
        )

    resolved = _resolve_transport(delivery_plan)
    if resolved.transport is None:
        reason = resolved.reason or "Email transport unavailable."
        return _skip_all(vessels, reason=reason, transport=resolved.name)

    root = _resolve_run_root(run_paths)
    eml_files = _list_eml_files(root)

    results: list[EmailDeliveryResult] = []

    for vessel in vessels:
        vessel_id = _coerce_vessel_id(vessel)
        if not vessel_id:
            results.append(
                EmailDeliveryResult(
                    vessel_id="UNKNOWN",
                    status="skipped",
                    reason="Missing vessel identifier.",
                    transport=resolved.name,
                    provider_message_id=None,
                )
            )
            continue

        eml_path = _resolve_eml_path(vessel, vessel_id, root, eml_files)
        if not eml_path or not eml_path.exists():
            results.append(
                EmailDeliveryResult(
                    vessel_id=vessel_id,
                    status="skipped",
                    reason="Missing .eml draft for vessel.",
                    transport=resolved.name,
                    provider_message_id=None,
                )
            )
            if logger:
                logger.warning("Email delivery skipped: missing draft for %s", vessel_id)
            continue

        result = _send_eml(resolved.transport, eml_path)
        if result.success:
            results.append(
                EmailDeliveryResult(
                    vessel_id=vessel_id,
                    status="sent",
                    reason=None,
                    transport=resolved.name,
                    provider_message_id=result.provider_message_id,
                )
            )
            if logger:
                logger.info("Email sent for %s", vessel_id)
            continue

        results.append(
            EmailDeliveryResult(
                vessel_id=vessel_id,
                status="failed",
                reason=result.error or "Email transport failed.",
                transport=resolved.name,
                provider_message_id=result.provider_message_id,
            )
        )
        if logger:
            logger.error("Email delivery failed for %s", vessel_id)

    # TODO: Append email delivery outcomes to summary.json in append-only fashion.
    return results


def _send_eml(transport: EmailTransport, eml_path: Path) -> TransportResult:
    try:
        return transport.send(eml_path)
    except Exception as exc:  # noqa: BLE001
        return TransportResult(
            success=False,
            provider_message_id=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def _resolve_transport(plan: object) -> _ResolvedTransport:
    name = _get_option(plan, "transport", None)
    if not name:
        return _ResolvedTransport(None, None, "No transport selected.")

    normalized = str(name).strip().lower()
    if normalized == "smtp":
        config = _coerce_smtp_config(_get_option(plan, "transport_config", None))
        if not config:
            config = _coerce_smtp_config(_get_option(plan, "smtp_config", None))
        if not config:
            return _ResolvedTransport(None, "smtp", "SMTP configuration missing.")
        return _ResolvedTransport(SmtpTransport(config), "smtp", None)

    if normalized in {"nicemail", "nice"}:
        # TODO: Wire Nicemail transport when available.
        return _ResolvedTransport(None, "nicemail", "Nicemail transport not implemented.")

    return _ResolvedTransport(None, normalized, "Unsupported transport selected.")


def _coerce_smtp_config(value: object) -> SmtpConfig | None:
    if isinstance(value, SmtpConfig):
        return value
    if isinstance(value, Mapping):
        try:
            return SmtpConfig(**value)
        except TypeError:
            return None
    return None


def _skip_all(
    vessels: Iterable[object], *, reason: str, transport: str | None
) -> list[EmailDeliveryResult]:
    return [
        EmailDeliveryResult(
            vessel_id=_coerce_vessel_id(vessel) or "UNKNOWN",
            status="skipped",
            reason=reason,
            transport=transport,
            provider_message_id=None,
        )
        for vessel in vessels
    ]


def _resolve_run_root(run_paths: object) -> Path:
    if isinstance(run_paths, (str, Path)):
        return Path(run_paths)
    for attr in ("output_dir", "run_dir"):
        if hasattr(run_paths, attr):
            value = getattr(run_paths, attr)
            if value:
                return Path(value)
    return Path(".")


def _list_eml_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.eml") if path.is_file())


def _resolve_eml_path(
    vessel: object,
    vessel_id: str,
    root: Path,
    eml_files: list[Path],
) -> Path | None:
    explicit = _extract_eml_path(vessel, root)
    if explicit and explicit.exists():
        return explicit

    normalized = vessel_id.strip().lower()
    exact = [path for path in eml_files if path.stem.lower() == normalized]
    if exact:
        return exact[0]

    contains = [path for path in eml_files if normalized and normalized in path.stem.lower()]
    if not contains:
        return None

    return sorted(contains, key=_path_sort_key)[0]


def _extract_eml_path(vessel: object, root: Path) -> Path | None:
    for key in ("eml_path", "draft_path", "eml_file", "eml_filename"):
        value = _get_option(vessel, key, None)
        if not value:
            continue
        path = Path(str(value))
        if not path.is_absolute():
            path = root / path
        return path
    return None


def _coerce_vessel_id(vessel: object) -> str:
    if isinstance(vessel, str):
        return vessel.strip()
    for key in ("ship_id", "vessel_id", "id"):
        value = _get_option(vessel, key, None)
        if value:
            return str(value).strip()
    return ""


def _get_option(container: object, name: str, default: object) -> object:
    if container is None:
        return default
    if isinstance(container, Mapping):
        return container.get(name, default)
    if hasattr(container, name):
        return getattr(container, name)
    return default


def _path_sort_key(path: Path) -> tuple[int, str]:
    return (len(path.stem), str(path))
