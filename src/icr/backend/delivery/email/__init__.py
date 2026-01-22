"""Email delivery utilities for Phase 7B."""

from .dispatch import EmailDeliveryPlan, EmailDeliveryResult, deliver_emails

__all__ = ["EmailDeliveryPlan", "EmailDeliveryResult", "deliver_emails"]
