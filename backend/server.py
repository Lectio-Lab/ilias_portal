"""Small localhost-only JSON API that preserves the legacy ILIAS endpoint paths."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import urllib.parse
from datetime import UTC, datetime
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from apps.ilias.client import IliasClient, IliasLoginError
from apps.ilias.security import validate_ilias_download_url
from state import StateCorruptionError, StateStore

MAX_BODY_BYTES = 25 * 1024 * 1024


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _string(data: dict[str, Any], name: str, *, required: bool = False, maximum: int | None = None) -> str | None:
    value = data.get(name)
    if value is None:
        if required:
            raise ApiError(400, f"{name} is required.")
        return None
    if not isinstance(value, str):
        raise ApiError(400, f"{name} must be a string.")
    if maximum is not None and len(value) > maximum:
        raise ApiError(400, f"{name} must be at most {maximum} characters.")
    return value


def _positive_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ApiError(400, f"{name} must be an integer.") from exc
    if parsed < 1:
        raise ApiError(400, f"{name} must be positive.")
    return parsed


def _deadline(value: str | None, name: str) -> str | None:
    if value in (None, ""):
        return value
    try:
        datetime.strptime(value, "%d.%m.%Y %H:%M")
    except ValueError as exc:
        raise ApiError(400, f"{name} must use DD.MM.YYYY HH:MM.") from exc
    return value


class PortalHandler(BaseHTTPRequestHandler):
    """Routes only authenticated local MCP requests; no public web surface exists."""

    server_version = "ILIASPortalLocal/1.0"

    @property
    def state(self) -> StateStore:
        return self.server.state  # type: ignore[attr-defined]

    @property
    def token(self) -> str:
        return self.server.token  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: object) -> None:
        # Request paths can contain course titles or URLs; retain only operational logs.
        print(f"[ilias-local] {self.command} {self.path.split('?', 1)[0]} -> {args[-2] if len(args) > 1 else ''}", file=sys.stderr)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        return header.startswith("Bearer ") and secrets.compare_digest(header[7:], self.token)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: int, detail: str) -> None:
        self._send_json(status, {"detail": detail})

    def _body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ApiError(400, "Content-Length must be an integer.") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ApiError(413, f"Request body must not exceed {MAX_BODY_BYTES} bytes.")
        return self.rfile.read(length)

    def _json_body(self) -> dict[str, Any]:
        raw = self._body()
        try:
            value = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            raise ApiError(400, "Request body must be valid JSON.") from exc
        if not isinstance(value, dict):
            raise ApiError(400, "Request body must be a JSON object.")
        return value

    def _multipart_body(self) -> tuple[dict[str, str], list[dict[str, Any]]]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data;"):
            raise ApiError(400, "Expected multipart/form-data.")
        envelope = (
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()
            + self._body()
        )
        message = BytesParser(policy=default).parsebytes(envelope)
        fields: dict[str, str] = {}
        files: list[dict[str, Any]] = []
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            content = part.get_payload(decode=True) or b""
            filename = part.get_filename()
            if filename:
                files.append({
                    "filename": Path(filename).name,
                    "content": content,
                    "content_type": part.get_content_type() or "application/octet-stream",
                    "title": Path(filename).name,
                    "description": "",
                })
            else:
                fields[name] = content.decode(part.get_content_charset() or "utf-8")
        return fields, files

    def _client_with_state(self, action: Callable[[IliasClient, dict[str, Any]], Any]) -> Any:
        # Holding this small advisory lock across login/action preserves the newest cookies.
        with self.state.locked():
            state = self.state.load()
            client = IliasClient(
                username="",
                password="",
                phpsessid=state["phpsessid"],
                shibsession=state["shibsession"],
            )
            client.login()
            state["phpsessid"] = client.phpsessid
            state["shibsession"] = client.shibsession
            self.state.save(state)
            return action(client, state)

    def _client(self, action: Callable[[IliasClient], Any]) -> Any:
        return self._client_with_state(lambda client, _state: action(client))

    def _route(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        if path == "/healthz" and self.command == "GET":
            self._send_json(200, {"status": "ok"})
            return
        if not self._authorized():
            raise ApiError(401, "Missing or invalid local bearer token.")

        if path == "/api/ilias/session/status/" and self.command == "GET":
            with self.state.locked():
                state = self.state.load()
            if not state["phpsessid"]:
                self._send_json(200, {"valid": False, "message": "No active ILIAS session. Refresh courses to open interactive university login."})
                return
            client = IliasClient("", "", phpsessid=state["phpsessid"], shibsession=state["shibsession"])
            try:
                valid = client.is_session_valid()
                message = "ILIAS session is active." if valid else "ILIAS session expired. Run course refresh to re-authenticate (MFA may be required)."
            except Exception as exc:
                valid, message = False, f"Session check failed: {exc}"
            self._send_json(200, {"valid": valid, "message": message})
            return

        if path == "/api/ilias/courses/" and self.command == "GET":
            with self.state.locked():
                courses = self.state.load()["course_cache"]
            self._send_json(200, {"count": len(courses), "courses": courses})
            return

        if path == "/api/ilias/courses/refresh/" and self.command == "POST":
            def refresh(client: IliasClient, state: dict[str, Any]) -> dict[str, Any]:
                courses = client.get_dashboard_courses()
                cached = [{
                    "course_id": course["id"], "title": course.get("title", ""),
                    "url": course.get("url", ""), "role": course.get("role", ""),
                    "last_refreshed": _now(),
                } for course in courses]
                state["course_cache"] = cached
                self.state.save(state)
                return {"count": len(cached), "courses": cached}
            self._send_json(200, self._client_with_state(refresh))
            return

        course_match = __import__("re").fullmatch(r"/api/ilias/courses/(\d+)/(.*)", path)
        if course_match:
            course_id = int(course_match.group(1))
            tail = course_match.group(2)
            if tail == "contents/" and self.command == "GET":
                self._send_json(200, self._client(lambda client: client.get_course_contents(course_id)))
                return
            if tail == "items/search/" and self.command == "GET":
                search = (query.get("q") or [""])[0].strip()
                if not search or len(search) > 500:
                    raise ApiError(400, "q is required and must be at most 500 characters.")
                limit = _positive_int((query.get("limit") or ["10"])[0], "limit")
                if limit > 20:
                    raise ApiError(400, "limit must be between 1 and 20.")
                item_type = (query.get("type") or [""])[0].strip() or None
                self._send_json(200, self._client(lambda client: client.find_course_items(course_id, search, item_type, limit)))
                return
            if tail == "items/exercise/" and self.command == "PATCH":
                self._send_json(200, self._client(lambda client: client.edit_exercise(course_id, **self._edit_data(self._json_body()))))
                return
            if tail == "grades/target/" and self.command == "GET":
                data = {key: (values or [""])[0] for key, values in query.items()}
                target = {"exercise_url": _string(data, "exercise_url", required=True), "assignment_id": _positive_int(data.get("assignment_id"), "assignment_id"), "participant_login": _string(data, "participant_login", required=True, maximum=255)}
                self._send_json(200, self._client(lambda client: client.get_grade_target(course_id, **target)))
                return
            if tail == "grades/" and self.command == "POST":
                self._send_json(200, self._client(lambda client: client.post_grade(course_id, **self._grade_data(self._json_body()))))
                return
            if tail == "publish/assignment/" and self.command == "POST":
                self._publish_assignment(course_id)
                return
            if tail == "publish/slides/" and self.command == "POST":
                self._publish_slides(course_id)
                return
            if tail == "publish/announcement/" and self.command == "POST":
                data = self._json_body()
                title = _string(data, "title", required=True, maximum=500)
                content = _string(data, "content", required=True)
                visibility = _string(data, "visibility") or "users"
                if visibility not in {"users", "public"}:
                    raise ApiError(400, "visibility must be users or public.")
                self._send_json(201, {"url": self._client(lambda client: client.publish_announcement(course_id, title, content, visibility))})
                return

        if path == "/api/ilias/download/" and self.command == "GET":
            raw_url = (query.get("url") or [""])[0]
            if not raw_url:
                raise ApiError(400, "Query parameter 'url' is required.")
            url = urllib.parse.unquote(raw_url)
            validate_ilias_download_url(url)
            content = self._client(lambda client: client.download_file(url))
            filename = Path(urllib.parse.urlparse(url).path).name or "download"
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        raise ApiError(404, "Unknown API endpoint.")

    def _edit_data(self, data: dict[str, Any]) -> dict[str, Any]:
        expected_title = _string(data, "expected_title", required=True, maximum=500)
        exercise_url = _string(data, "exercise_url", required=True)
        editable = ("title", "description", "assignment_title", "instruction", "deadline")
        if not any(name in data for name in editable):
            raise ApiError(400, "Provide at least one field to edit.")
        for replacement, expected in (("description", "expected_description"), ("assignment_title", "expected_assignment_title"), ("instruction", "expected_instruction"), ("deadline", "expected_deadline")):
            if replacement in data and expected not in data:
                raise ApiError(400, f"{expected} is required when changing {replacement}.")
        result: dict[str, Any] = {"exercise_url": exercise_url, "expected_title": expected_title}
        for name in ("expected_description", "expected_assignment_title", "expected_instruction", "title", "description", "assignment_title", "instruction"):
            if name in data:
                result[name] = _string(data, name, maximum=500 if "title" in name else None)
        for name in ("expected_deadline", "deadline"):
            if name in data:
                value = _string(data, name)
                result[name] = _deadline(value, name)
        if "assignment_id" in data:
            result["assignment_id"] = _positive_int(data["assignment_id"], "assignment_id")
        return result

    def _grade_data(self, data: dict[str, Any]) -> dict[str, Any]:
        required = ("exercise_url", "expected_exercise_title", "expected_assignment_title", "expected_status", "expected_mark")
        result = {name: _string(data, name, required=True, maximum=500 if "title" in name else 32 if name == "expected_mark" else None) for name in required}
        result["assignment_id"] = _positive_int(data.get("assignment_id"), "assignment_id")
        result["participant_login"] = _string(data, "participant_login", required=True, maximum=255)
        result["expected_comment"] = _string(data, "expected_comment")
        if result["expected_status"] not in {"notgraded", "passed", "failed"}:
            raise ApiError(400, "expected_status is invalid.")
        if not any(name in data for name in ("status", "mark", "comment")):
            raise ApiError(400, "Provide at least one grade field to update.")
        for name in ("status", "mark", "comment"):
            if name in data:
                result[name] = _string(data, name, maximum=32 if name == "mark" else None)
        if "status" in result and result["status"] not in {"notgraded", "passed", "failed"}:
            raise ApiError(400, "status is invalid.")
        return result

    def _publish_assignment(self, course_id: int) -> None:
        if self.headers.get("Content-Type", "").startswith("multipart/form-data;"):
            fields, files = self._multipart_body()
            file = files[0] if files else None
        else:
            fields, file = self._json_body(), None
        title = _string(fields, "title", required=True, maximum=500)
        instruction = _string(fields, "instruction", required=True)
        deadline = _deadline(_string(fields, "deadline"), "deadline")
        result = self._client(lambda client: client.publish_assignment(course_id, title, instruction, deadline or None, file["filename"] if file else "", file["content"] if file else None, file["content_type"] if file else "application/octet-stream"))
        self._send_json(201, {"url": result})

    def _publish_slides(self, course_id: int) -> None:
        fields, files = self._multipart_body()
        title = _string(fields, "title", required=True, maximum=500)
        description = _string(fields, "description") or ""
        result = self._client(lambda client: client.publish_slides(course_id, title, description, files))
        self._send_json(201, {"url": result})

    def _dispatch(self) -> None:
        try:
            self._route()
        except ApiError as exc:
            self._send_error(exc.status, exc.detail)
        except (ValueError, IliasLoginError) as exc:
            self._send_error(422, str(exc))
        except StateCorruptionError as exc:
            self._send_error(500, str(exc))
        except Exception as exc:
            self._send_error(502, f"ILIAS operation failed: {exc}")

    do_GET = _dispatch
    do_POST = _dispatch
    do_PATCH = _dispatch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("BACKEND_PORT", "8010")))
    parser.add_argument("--state-file", default=os.environ.get("ILIAS_STATE_FILE", ""))
    args = parser.parse_args()
    token = os.environ.get("PORTAL_LOCAL_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("PORTAL_LOCAL_TOKEN is missing or too short; run ./install.sh to provision it.")
    state_file = args.state_file or str(Path(__file__).parent / "../agent/credentials/ilias-state.json")
    # The constructor receives the fixed loopback address: callers cannot expose it.
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), PortalHandler)
    httpd.token = token  # type: ignore[attr-defined]
    httpd.state = StateStore(state_file)  # type: ignore[attr-defined]
    print(f"ILIAS local service listening on http://127.0.0.1:{args.port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
