"""Owner-only, atomic local state for the single-user agent kit."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


class StateCorruptionError(RuntimeError):
    """Raised after preserving a state file that cannot safely be read."""


class StateStore:
    """Serialize all state access so concurrent local requests cannot lose cookies."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(".lock")

    @staticmethod
    def empty() -> dict[str, Any]:
        return {
            "ilias_username": "",
            "phpsessid": "",
            "shibsession": "",
            "course_cache": [],
        }

    def _prepare_directory(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # The credentials directory also contains the local bearer token.
        os.chmod(self.path.parent, 0o700)

    @contextmanager
    def locked(self) -> Iterator[None]:
        self._prepare_directory()
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.chmod(self.lock_path, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self.empty()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise self._preserve_corrupt_state() from exc
        if not isinstance(raw, dict):
            raise self._preserve_corrupt_state()

        state = self.empty()
        for key in ("ilias_username", "phpsessid", "shibsession"):
            if isinstance(raw.get(key), str):
                state[key] = raw[key]
        if isinstance(raw.get("course_cache"), list):
            state["course_cache"] = [
                item for item in raw["course_cache"] if isinstance(item, dict)
            ]
        return state

    def _preserve_corrupt_state(self) -> StateCorruptionError:
        backup = self.path.with_name(
            f"{self.path.name}.corrupt-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )
        shutil.copy2(self.path, backup)
        os.chmod(backup, 0o600)
        return StateCorruptionError(
            f"Local ILIAS state is corrupt and was preserved at {backup}. "
            "Repair or remove the state file before retrying."
        )

    def save(self, state: dict[str, Any]) -> None:
        self._prepare_directory()
        payload = json.dumps(state, indent=2, sort_keys=True) + "\n"
        descriptor, temporary_path = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp"
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            # Replace is atomic within one directory, preventing partial cookie files.
            os.replace(temporary_path, self.path)
            os.chmod(self.path, 0o600)
        except Exception:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            raise
