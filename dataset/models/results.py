"""Structured results for watched record operations."""

from dataclasses import dataclass


@dataclass
class AddRecordResult:
    ok: bool
    title: str | None
    message: str
    reason: str | None = None


@dataclass
class UpdateRecordResult:
    ok: bool
    title: str | None
    message: str
    reason: str | None = None
    changed_fields: list[str] | None = None


@dataclass
class DeleteRecordResult:
    ok: bool
    dataset_key: str | None
    message: str
    reason: str | None = None
