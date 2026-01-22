from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from icr.backend.delivery.email import dispatch
from icr.backend.delivery.email.models import EmailDeliveryPlan
from icr.backend.delivery.email.transports.base import TransportResult


@dataclass
class FakeRunPaths:
    output_dir: Path


class FakeEmailTransport:
    def __init__(self, *, fail_on: set[Path] | None = None, raise_on: set[Path] | None = None) -> None:
        self.fail_on = fail_on or set()
        self.raise_on = raise_on or set()
        self.calls: list[Path] = []

    @property
    def name(self) -> str:
        return "fake"

    def send(self, eml_path: Path) -> TransportResult:
        self.calls.append(eml_path)
        if eml_path in self.raise_on:
            raise RuntimeError("boom")
        if eml_path in self.fail_on:
            return TransportResult(success=False, provider_message_id=None, error="failed")
        return TransportResult(success=True, provider_message_id="msg-123", error=None)


@pytest.fixture
def run_paths(tmp_path: Path) -> FakeRunPaths:
    return FakeRunPaths(output_dir=tmp_path / "output")


@pytest.fixture
def vessels() -> list[dict[str, str]]:
    return [
        {"ship_id": "VESSEL_A", "eml_filename": "emails/VESSEL_A.eml"},
        {"ship_id": "VESSEL_B", "eml_filename": "emails/VESSEL_B.eml"},
    ]


@pytest.fixture
def eml_drafts(run_paths: FakeRunPaths, vessels: list[dict[str, str]]) -> dict[str, Path]:
    drafts_dir = run_paths.output_dir / "emails"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    created: dict[str, Path] = {}
    for vessel in vessels:
        path = drafts_dir / f"{vessel['ship_id']}.eml"
        path.write_bytes(b"DUMMY-EML")
        created[vessel["ship_id"]] = path
    return created


def test_email_delivery_disabled_skips_all(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    def _no_transport(_: object) -> dispatch._ResolvedTransport:  # type: ignore[attr-defined]
        raise AssertionError("transport should not be resolved")

    monkeypatch.setattr(dispatch, "_resolve_transport", _no_transport)

    results = dispatch.deliver_emails(
        run_paths,
        vessels,
        EmailDeliveryPlan(send_now=False, confirm_send=False, transport="smtp"),
        logger=None,
    )

    assert len(results) == len(vessels)
    assert all(result.status == "skipped" for result in results)
    assert all("disabled" in (result.reason or "").lower() for result in results)


def test_email_delivery_not_confirmed(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    def _no_transport(_: object) -> dispatch._ResolvedTransport:  # type: ignore[attr-defined]
        raise AssertionError("transport should not be resolved")

    monkeypatch.setattr(dispatch, "_resolve_transport", _no_transport)

    results = dispatch.deliver_emails(
        run_paths,
        vessels,
        EmailDeliveryPlan(send_now=True, confirm_send=False, transport="smtp"),
        logger=None,
    )

    assert len(results) == len(vessels)
    assert all(result.status == "skipped" for result in results)
    assert all("confirm" in (result.reason or "").lower() for result in results)


def test_email_missing_draft_is_skipped(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    missing_vessel = {"ship_id": "VESSEL_C", "eml_filename": "emails/VESSEL_C.eml"}
    all_vessels = vessels + [missing_vessel]

    transport = FakeEmailTransport()
    monkeypatch.setattr(
        dispatch,
        "_resolve_transport",
        lambda _: dispatch._ResolvedTransport(transport, "fake", None),  # type: ignore[attr-defined]
    )

    results = dispatch.deliver_emails(
        run_paths,
        all_vessels,
        EmailDeliveryPlan(send_now=True, confirm_send=True, transport="fake"),
        logger=None,
    )

    by_vessel = {result.vessel_id: result for result in results}
    assert by_vessel["VESSEL_C"].status == "skipped"
    assert "draft" in (by_vessel["VESSEL_C"].reason or "").lower()
    assert by_vessel["VESSEL_A"].status == "sent"
    assert by_vessel["VESSEL_B"].status == "sent"
    assert transport.calls == [eml_drafts["VESSEL_A"], eml_drafts["VESSEL_B"]]


def test_email_delivery_success(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    transport = FakeEmailTransport()
    monkeypatch.setattr(
        dispatch,
        "_resolve_transport",
        lambda _: dispatch._ResolvedTransport(transport, "fake", None),  # type: ignore[attr-defined]
    )

    results = dispatch.deliver_emails(
        run_paths,
        vessels,
        EmailDeliveryPlan(send_now=True, confirm_send=True, transport="fake"),
        logger=None,
    )

    assert len(results) == len(vessels)
    assert all(result.status == "sent" for result in results)
    assert all(result.provider_message_id == "msg-123" for result in results)
    assert transport.calls == [eml_drafts["VESSEL_A"], eml_drafts["VESSEL_B"]]


def test_email_delivery_failure_isolated(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    transport = FakeEmailTransport(raise_on={eml_drafts["VESSEL_B"]})
    monkeypatch.setattr(
        dispatch,
        "_resolve_transport",
        lambda _: dispatch._ResolvedTransport(transport, "fake", None),  # type: ignore[attr-defined]
    )

    results = dispatch.deliver_emails(
        run_paths,
        vessels,
        EmailDeliveryPlan(send_now=True, confirm_send=True, transport="fake"),
        logger=None,
    )

    by_vessel = {result.vessel_id: result for result in results}
    assert by_vessel["VESSEL_B"].status == "failed"
    assert by_vessel["VESSEL_A"].status == "sent"
    assert len(results) == len(vessels)


def test_email_transport_routing(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    created: dict[str, object] = {}

    class FakeSmtpTransport:
        name = "smtp"

        def __init__(self, config: object) -> None:
            created["config"] = config

        def send(self, eml_path: Path) -> TransportResult:
            return TransportResult(success=True, provider_message_id=None, error=None)

    monkeypatch.setattr(dispatch, "SmtpTransport", FakeSmtpTransport)

    plan = EmailDeliveryPlan(
        send_now=True,
        confirm_send=True,
        transport="smtp",
        transport_config={
            "host": "example.com",
            "port": 587,
            "envelope_from": "sender@example.com",
            "envelope_to": ("rcpt@example.com",),
        },
    )

    results = dispatch.deliver_emails(run_paths, vessels[:1], plan, logger=None)

    assert "config" in created
    assert len(results) == 1
    assert results[0].status == "sent"


def test_email_delivery_does_not_modify_eml(
    run_paths: FakeRunPaths, vessels: list[dict[str, str]], eml_drafts: dict[str, Path], monkeypatch
) -> None:
    transport = FakeEmailTransport()
    monkeypatch.setattr(
        dispatch,
        "_resolve_transport",
        lambda _: dispatch._ResolvedTransport(transport, "fake", None),  # type: ignore[attr-defined]
    )

    eml_path = eml_drafts["VESSEL_A"]
    before_bytes = eml_path.read_bytes()
    before_mtime = eml_path.stat().st_mtime_ns

    dispatch.deliver_emails(
        run_paths,
        vessels,
        EmailDeliveryPlan(send_now=True, confirm_send=True, transport="fake"),
        logger=None,
    )

    after_bytes = eml_path.read_bytes()
    after_mtime = eml_path.stat().st_mtime_ns

    assert before_bytes == after_bytes
    assert before_mtime == after_mtime
