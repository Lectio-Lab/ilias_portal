"""
IliasClient — per-user ILIAS session client.

Performs a headless Shibboleth SSO login via requests (no Playwright dependency
at runtime). All mutating operations (publish assignment, slides, announcement)
are ported from the original OvidiusClient in scaping.py.
"""

import os
import re
import time
import unicodedata
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://ovidius.uni-tuebingen.de"
DEFAULT_CLIENT_ID = "pr02"
SHIBSESSION_COOKIE_NAME = (
    "_shibsession_64656661756c7468747470733a2f2f6f7669646975732e756e692d74756562696e67656e"
    "2e64652f73686962626f6c6574682d7370"
)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) "
        "Gecko/20100101 Firefox/115.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
_UNSET = object()


class IliasLoginError(Exception):
    """Raised when login fails (bad credentials, MFA required, etc.)."""


class IliasClient:
    """
    Per-user ILIAS client.  Call ``login()`` before any other method.
    """

    def __init__(
        self,
        username: str,
        password: str,
        client_id: str = DEFAULT_CLIENT_ID,
        phpsessid: Optional[str] = None,
        shibsession: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.phpsessid = phpsessid
        self.shibsession = shibsession
        self.session = requests.Session()
        self.session.headers.update(_BROWSER_HEADERS)
        if phpsessid and shibsession:
            self._configure_session()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> bool:
        """
        Attempt a silent headless Shibboleth SSO login.
        If it fails (e.g. because of MFA), falls back to interactive Playwright login.
        Returns True on success, False on failure.
        Populates ``self.phpsessid`` and ``self.shibsession`` and configures
        the internal requests.Session with the necessary cookies.
        """
        # If we already have cookies passed in and they are valid, skip login
        if self.phpsessid and self.shibsession and self.is_session_valid():
            return True

        phpsessid = None
        shibsession = None

        try:
            if not self.username or not self.password:
                raise IliasLoginError(
                    "No university credentials are stored; interactive login required."
                )
            session = requests.Session()
            session.headers.update(_BROWSER_HEADERS)

            # Step 1: Hit shib_login.php — this redirects through Shibboleth IdP
            init_url = f"{BASE_URL}/shib_login.php"
            res = session.get(init_url, allow_redirects=True)

            soup = BeautifulSoup(res.text, "html.parser")
            form = soup.find("form")
            if not form:
                raise IliasLoginError(
                    "No login form found — MFA or anti-bot page may have loaded."
                )

            action_url = urljoin(res.url, form.get("action", ""))

            # Step 2: Build the form payload, injecting credentials
            payload: dict = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                if not name:
                    continue
                inp_type = inp.get("type", "")
                if inp_type == "password" or "password" in name.lower():
                    payload[name] = self.password
                elif (
                    "user" in name.lower()
                    or "login" in name.lower()
                    or inp_type == "text"
                ):
                    payload[name] = self.username
                else:
                    payload[name] = inp.get("value", "")

            # Step 3: Submit credentials
            res2 = session.post(action_url, data=payload, allow_redirects=True)

            # Step 4: Follow SAML assertion redirect if present
            soup2 = BeautifulSoup(res2.text, "html.parser")
            saml_form = soup2.find("form")
            if saml_form:
                action_attr = saml_form.get("action", "")
                if "saml" in action_attr.lower() or "shibboleth" in action_attr.lower():
                    saml_action_url = urljoin(res2.url, action_attr)
                    saml_payload = {
                        inp.get("name"): inp.get("value", "")
                        for inp in saml_form.find_all("input")
                        if inp.get("name")
                    }
                    res2 = session.post(
                        saml_action_url, data=saml_payload, allow_redirects=True
                    )

            # Step 5: Extract session cookies
            phpsessid = session.cookies.get(
                "PHPSESSID", domain="ovidius.uni-tuebingen.de"
            )
            shibsession = None
            for cookie in session.cookies:
                if "shibsession" in cookie.name and "ovidius" in cookie.domain:
                    shibsession = cookie.value
                    break

        except Exception as exc:
            print(f"Headless login failed/MFA required: {exc}")

        # Fallback: Launch Interactive Playwright Browser
        if not phpsessid or not shibsession:
            from playwright.sync_api import sync_playwright

            print(
                "\n[Playwright] A browser window will open for university login and MFA..."
            )
            try:
                with sync_playwright() as p:
                    launch_kwargs: dict = {"headless": False}
                    channel = os.environ.get("PLAYWRIGHT_BROWSER_CHANNEL", "").strip()
                    executable = os.environ.get(
                        "PLAYWRIGHT_EXECUTABLE_PATH", ""
                    ).strip()
                    if channel:
                        launch_kwargs["channel"] = channel
                    elif executable:
                        launch_kwargs["executable_path"] = executable

                    browser = p.chromium.launch(**launch_kwargs)
                    context = browser.new_context()
                    page = context.new_page()

                    print("[Playwright] Navigating to login page...")
                    page.goto(f"{BASE_URL}/shib_login.php", wait_until="networkidle")

                    print(
                        "[Playwright] Complete login and MFA in the browser window."
                    )
                    print("[Playwright] Waiting for login completion (checking session cookies)...")

                    # Pre-fill only when the user explicitly configured credentials.
                    # Interactive-only mode leaves both fields untouched.
                    try:
                        page.wait_for_selector("input[type='password']", timeout=5000)
                        user_input = page.locator("input[type='text'], input[name*='user' i], input[name*='login' i]")
                        pass_input = page.locator("input[type='password']")
                        if user_input.count() > 0 and self.username:
                            user_input.first.fill(self.username)
                        if pass_input.count() > 0 and self.password:
                            pass_input.first.fill(self.password)
                    except Exception:
                        pass

                    # Poll for cookies (timeout in 180 seconds / 3 minutes)
                    timeout = 180
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        cookies = context.cookies()
                        for c in cookies:
                            if c["name"] == "PHPSESSID" and "ovidius" in c["domain"]:
                                phpsessid = c["value"]
                            elif "shibsession" in c["name"] and "ovidius" in c["domain"]:
                                shibsession = c["value"]

                        if phpsessid and shibsession:
                            break

                        time.sleep(1.0)

                    browser.close()
            except Exception as playwright_exc:
                raise IliasLoginError(f"Interactive browser login failed: {playwright_exc}") from playwright_exc

        if not phpsessid or not shibsession:
            raise IliasLoginError(
                "Session cookies missing after login — MFA challenge likely required."
            )

        # Commit to the instance
        self.phpsessid = phpsessid
        self.shibsession = shibsession
        self._configure_session()
        return True

    def _configure_session(self, src_session: Optional[requests.Session] = None):
        """Apply ILIAS cookies and browser headers to the instance session."""
        self.session = requests.Session()
        self.session.headers.update(_BROWSER_HEADERS)
        self.session.cookies.set(
            "PHPSESSID", self.phpsessid, domain="ovidius.uni-tuebingen.de"
        )
        self.session.cookies.set(
            "ilClientId", self.client_id, domain="ovidius.uni-tuebingen.de"
        )
        self.session.cookies.set(
            SHIBSESSION_COOKIE_NAME, self.shibsession, domain="ovidius.uni-tuebingen.de"
        )
        if src_session is not None:
            # Merge any extra cookies from the login session
            for cookie in src_session.cookies:
                self.session.cookies.set(
                    cookie.name, cookie.value, domain=cookie.domain
                )

    # ------------------------------------------------------------------
    # Session validation
    # ------------------------------------------------------------------

    def is_session_valid(self) -> bool:
        """Return True if current session cookies are accepted by ILIAS."""
        try:
            url = f"{BASE_URL}/ilias.php?baseClass=ilDashboardGUI"
            res = self.session.get(url, allow_redirects=False)
            if res.status_code in (301, 302):
                location = res.headers.get("Location", "")
                if "login" in location or "shib" in location:
                    return False
            return res.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Dashboard / course discovery
    # ------------------------------------------------------------------

    def get_dashboard_courses(self) -> list:
        """
        Scrape the ILIAS dashboard for courses.
        Returns a list of dicts: {id, title, url, role}.
        """
        url = f"{BASE_URL}/ilias.php?baseClass=ilDashboardGUI"
        res = self.session.get(url, allow_redirects=True)
        if "login.php" in res.url or "shib_login.php" in res.url:
            raise IliasLoginError("Session expired while fetching dashboard.")

        return self._parse_course_list(res.text)

    def get_moderator_courses(self) -> list:
        """
        Return courses where the authenticated user has admin/tutor/moderator access.
        Fetches the "My Courses & Groups" panel from the dashboard.
        """
        url = f"{BASE_URL}/ilias.php?baseClass=ilDashboardGUI&cmd=jumpToSelectedItems"
        res = self.session.get(url, allow_redirects=True)
        if "login.php" in res.url or "shib_login.php" in res.url:
            raise IliasLoginError("Session expired while fetching moderator courses.")

        all_courses = self._parse_course_list(res.text)
        # Filter to courses where we have write access (admin / tutor role)
        return [
            c
            for c in all_courses
            if c.get("role", "").lower()
            in ("admin", "tutor", "moderator", "instructor", "")
        ]

    def _parse_course_list(self, html: str) -> list:
        """
        Parse an ILIAS page and extract all course items.
        Each item: {id, title, url, role}.
        """
        soup = BeautifulSoup(html, "html.parser")
        courses = []

        for item in soup.select(
            ".il-item-title a, .il_ContainerItemTitle a, h3.il_ContainerItemTitle a"
        ):
            href = item.get("href", "")
            title = item.get_text(strip=True)
            if not title or not href:
                continue

            full_url = urljoin(BASE_URL, href)
            course_id = self._extract_ref_id(full_url)
            if course_id is None:
                # Try goto.php style
                m = re.search(r"/goto\.php/crs/(\d+)", href)
                if m:
                    course_id = int(m.group(1))

            # Try to detect role from surrounding markup
            role = ""
            parent = item.find_parent(
                class_=re.compile(r"il-std-item|ilObjListRow|il-item")
            )
            if parent:
                role_tag = parent.find(
                    class_=re.compile(r"il-item-description|il_ItemProperty")
                )
                if role_tag:
                    role = role_tag.get_text(strip=True).lower()

            if course_id is not None:
                courses.append(
                    {"id": course_id, "title": title, "url": full_url, "role": role}
                )

        # Deduplicate by course_id
        seen: set = set()
        unique: list = []
        for c in courses:
            if c["id"] not in seen:
                seen.add(c["id"])
                unique.append(c)

        return unique

    # ------------------------------------------------------------------
    # Course content
    # ------------------------------------------------------------------

    def get_course_contents(self, course_id: int) -> dict:
        """
        Fetch and parse a course page.
        Returns {course_title, sections: [{section, items: [{title, url, type, properties}]}]}.
        """
        url = f"{BASE_URL}/goto.php/crs/{course_id}"
        res = self.session.get(url, allow_redirects=True)
        if "login.php" in res.url or "shib_login.php" in res.url:
            raise IliasLoginError("Session expired while fetching course contents.")
        res.raise_for_status()
        return self._parse_course(res.text)

    def _parse_course(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        result: dict = {"course_title": None, "sections": []}

        title_tag = soup.find("h1")
        if title_tag:
            result["course_title"] = title_tag.get_text(strip=True)

        for section in soup.select("div.ilContainerBlock"):
            header = section.select_one(".ilContainerBlockHeader h2")
            section_name = header.get_text(strip=True) if header else "Unknown"
            items = []
            for row in section.select(".ilObjListRow"):
                link = row.select_one("h3.il_ContainerItemTitle a")
                if not link:
                    continue
                item = {
                    "title": link.get_text(strip=True),
                    "url": urljoin(BASE_URL, link.get("href", "")),
                    "type": None,
                    "properties": {},
                }
                icon = row.select_one(".ilContainerListItemIcon img")
                if icon:
                    item["type"] = icon.get("alt", "")
                for idx, prop in enumerate(row.select(".il_ItemProperty"), start=1):
                    item["properties"][f"property_{idx}"] = prop.get_text(
                        " ", strip=True
                    )
                items.append(item)

            result["sections"].append({"section": section_name, "items": items})

        return result

    def find_course_items(
        self,
        course_id: int,
        query: str,
        item_type: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        """Find live course items by title, type, section, and visible properties."""
        query_normalized = self._normalize_search_text(query)
        if not query_normalized:
            raise ValueError("Search query must not be empty.")

        type_normalized = self._normalize_search_text(item_type or "")
        contents = self.get_course_contents(course_id)
        matches = []

        for section in contents.get("sections", []):
            section_name = section.get("section", "")
            for item in section.get("items", []):
                title = item.get("title", "")
                item_type_value = item.get("type") or ""
                if type_normalized and type_normalized not in self._normalize_search_text(
                    item_type_value
                ):
                    continue

                properties = " ".join((item.get("properties") or {}).values())
                title_normalized = self._normalize_search_text(title)
                searchable = self._normalize_search_text(
                    " ".join(
                        [title, item_type_value, section_name, properties]
                    )
                )
                score, reason = self._search_score(
                    query_normalized, title_normalized, searchable
                )
                if score <= 0:
                    continue

                match = {
                    **item,
                    "section": section_name,
                    "ref_id": self._extract_object_ref_id(item.get("url", "")),
                    "match_score": score,
                    "match_reason": reason,
                }
                matches.append(match)

        matches.sort(
            key=lambda match: (-match["match_score"], match["title"].casefold())
        )
        bounded_limit = max(1, min(limit, 20))
        returned_matches = matches[:bounded_limit]
        for match in returned_matches:
            if self._is_exercise_item(match):
                try:
                    match["content"] = self.get_exercise_details(match["url"])
                except (ValueError, requests.RequestException) as exc:
                    match["content_error"] = str(exc)
        return {
            "course_id": course_id,
            "course_title": contents.get("course_title"),
            "query": query,
            "count": len(returned_matches),
            "total_matches": len(matches),
            "matches": returned_matches,
        }

    def get_exercise_details(self, exercise_url: str) -> dict:
        """Fetch current exercise settings and assignment units without changing them."""
        ref_id = self._exercise_ref_id(exercise_url)
        canonical_url = f"{BASE_URL}/goto.php/exc/{ref_id}"
        settings_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilexercisehandlergui"
            f"&cmdNode=cp:o6&cmdClass=ilObjExerciseGUI&cmd=edit&ref_id={ref_id}"
        )
        settings_response = self.session.get(settings_url, allow_redirects=True)
        self._raise_for_ilias_response(settings_response, "fetch exercise settings")
        settings_soup = BeautifulSoup(settings_response.text, "html.parser")
        settings_form = self._find_form_with_field(settings_soup, "title", "desc")

        title_tag = settings_soup.find("h1")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""
        description = None
        editable = settings_form is not None
        if settings_form is not None:
            title_input = settings_form.find("input", {"name": "title"})
            description_input = settings_form.find("textarea", {"name": "desc"})
            if title_input is not None:
                title = title_input.get("value", "")
            if description_input is not None:
                description = description_input.get_text()

        assignments_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilexercisehandlergui"
            f"&cmdNode=cp:o6:c1&cmdClass=ilExAssignmentEditorGUI"
            f"&cmd=listAssignments&ref_id={ref_id}&from_overview=1"
        )
        assignments_response = self.session.get(assignments_url, allow_redirects=True)
        self._raise_for_ilias_response(assignments_response, "fetch assignment list")
        assignments_soup = BeautifulSoup(assignments_response.text, "html.parser")

        assignments = []
        seen_assignment_ids = set()
        for link in assignments_soup.find_all("a", href=True):
            href = urljoin(assignments_response.url, link.get("href", ""))
            params = parse_qs(urlparse(href).query)
            if params.get("cmd") != ["editAssignment"] or not params.get("ass_id"):
                continue
            try:
                assignment_id = int(params["ass_id"][0])
            except (TypeError, ValueError):
                continue
            if assignment_id in seen_assignment_ids:
                continue
            seen_assignment_ids.add(assignment_id)
            assignments.append(self._get_assignment_details(href, assignment_id))

        return {
            "ref_id": ref_id,
            "title": title,
            "description": description,
            "url": canonical_url,
            "editable": editable,
            "assignments": assignments,
        }

    def edit_exercise(
        self,
        course_id: int,
        exercise_url: str,
        expected_title: str,
        expected_description=_UNSET,
        expected_assignment_title=_UNSET,
        expected_instruction=_UNSET,
        expected_deadline=_UNSET,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignment_id: Optional[int] = None,
        assignment_title: Optional[str] = None,
        instruction: Optional[str] = None,
        deadline: Optional[str] = None,
    ) -> dict:
        """Edit an exact exercise, then re-fetch and verify every requested change."""
        ref_id = self._exercise_ref_id(exercise_url)
        canonical_url = f"{BASE_URL}/goto.php/exc/{ref_id}"
        requested_fields = {
            "title": title,
            "description": description,
            "assignment_title": assignment_title,
            "instruction": instruction,
            "deadline": deadline,
        }
        changed_fields = [
            field for field, value in requested_fields.items() if value is not None
        ]
        if not changed_fields:
            raise ValueError("At least one exercise field must be provided for editing.")

        course_contents = self.get_course_contents(course_id)
        target_item = next(
            (
                item
                for section in course_contents.get("sections", [])
                for item in section.get("items", [])
                if self._extract_object_ref_id(item.get("url", "")) == ref_id
            ),
            None,
        )
        if target_item is None or not self._is_exercise_item(target_item):
            raise ValueError(
                "The exercise URL is not an exercise in the requested course. "
                "Run ilias_find_course_items again and use its exact URL."
            )

        before = self.get_exercise_details(canonical_url)
        if before["title"].strip() != expected_title.strip():
            raise ValueError(
                f'Exercise title changed or does not match: expected "{expected_title}", '
                f'found "{before["title"]}". Re-run ilias_find_course_items before editing.'
            )
        if description is not None:
            if expected_description is _UNSET:
                raise ValueError(
                    "expected_description is required when changing the description."
                )
            if before["description"] != expected_description:
                raise ValueError(
                    "Exercise description changed since discovery. "
                    "Re-run ilias_find_course_items before editing."
                )
        if not before["editable"]:
            raise ValueError("ILIAS did not expose editable settings for this exercise.")

        assignment_changes_requested = any(
            value is not None
            for value in (assignment_title, instruction, deadline)
        )
        selected_assignment = None
        if assignment_changes_requested:
            assignments = before["assignments"]
            if assignment_id is not None:
                selected_assignment = next(
                    (
                        assignment
                        for assignment in assignments
                        if assignment["id"] == assignment_id
                    ),
                    None,
                )
                if selected_assignment is None:
                    raise ValueError(
                        f"Assignment ID {assignment_id} is not part of this exercise."
                    )
            elif len(assignments) == 1:
                selected_assignment = assignments[0]
            elif not assignments:
                raise ValueError("This exercise has no editable assignment unit.")
            else:
                choices = ", ".join(
                    f'{assignment["id"]}: {assignment["title"]}'
                    for assignment in assignments
                )
                raise ValueError(
                    "This exercise contains multiple assignment units. "
                    f"Choose assignment_id from: {choices}."
                )

            expected_assignment_fields = (
                ("assignment_title", assignment_title, expected_assignment_title),
                ("instruction", instruction, expected_instruction),
                ("deadline", deadline, expected_deadline),
            )
            for field_name, replacement, expected in expected_assignment_fields:
                if replacement is None:
                    continue
                if expected is _UNSET:
                    raise ValueError(
                        f"expected_{field_name} is required when changing {field_name}."
                    )
                if selected_assignment[field_name.replace("assignment_", "")] != expected:
                    raise ValueError(
                        f"Assignment {field_name} changed since discovery. "
                        "Re-run ilias_find_course_items before editing."
                    )

        # Update the assignment first so an assignment validation error cannot follow
        # a successful container rename in the common combined-edit case.
        if selected_assignment is not None:
            self._update_assignment(
                selected_assignment["edit_url"],
                assignment_title=assignment_title,
                instruction=instruction,
                deadline=deadline,
            )
        if title is not None or description is not None:
            self._update_exercise_settings(
                ref_id, title=title, description=description
            )

        updated = self.get_exercise_details(canonical_url)
        verification_errors = []
        if title is not None and updated["title"] != title:
            verification_errors.append("title")
        if description is not None and updated["description"] != description:
            verification_errors.append("description")

        updated_assignment = None
        if selected_assignment is not None:
            updated_assignment = next(
                (
                    assignment
                    for assignment in updated["assignments"]
                    if assignment["id"] == selected_assignment["id"]
                ),
                None,
            )
            if updated_assignment is None:
                verification_errors.append("assignment")
            else:
                if (
                    assignment_title is not None
                    and updated_assignment["title"] != assignment_title
                ):
                    verification_errors.append("assignment_title")
                if (
                    instruction is not None
                    and updated_assignment["instruction"] != instruction
                ):
                    verification_errors.append("instruction")
                expected_deadline = deadline or None
                if (
                    deadline is not None
                    and updated_assignment["deadline"] != expected_deadline
                ):
                    verification_errors.append("deadline")

        if verification_errors:
            raise ValueError(
                "ILIAS accepted the request but verification failed for: "
                + ", ".join(verification_errors)
            )

        return {
            "success": True,
            "verified": True,
            "url": canonical_url,
            "updated_fields": changed_fields,
            "exercise": {
                key: value
                for key, value in updated.items()
                if key != "assignments"
            },
            "assignment": updated_assignment,
        }

    def _update_exercise_settings(
        self,
        ref_id: int,
        title: Optional[str],
        description: Optional[str],
    ) -> None:
        settings_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilexercisehandlergui"
            f"&cmdNode=cp:o6&cmdClass=ilObjExerciseGUI&cmd=edit&ref_id={ref_id}"
        )
        response = self.session.get(settings_url, allow_redirects=True)
        self._raise_for_ilias_response(response, "open exercise settings")
        soup = BeautifulSoup(response.text, "html.parser")
        form = self._find_form_with_field(soup, "title", "desc")
        if form is None:
            raise ValueError(
                "Could not find editable exercise settings. Check your ILIAS role."
            )

        payload = self._form_payload(form)
        if title is not None:
            payload = self._set_form_field(payload, "title", title)
        if description is not None:
            payload = self._set_form_field(payload, "desc", description)
        payload = self._set_form_field(payload, "cmd[update]", "Save")
        action_url = urljoin(response.url, form.get("action", ""))
        result = self.session.post(action_url, data=payload, allow_redirects=True)
        self._raise_for_ilias_response(result, "update exercise settings")

    def _update_assignment(
        self,
        edit_url: str,
        assignment_title: Optional[str],
        instruction: Optional[str],
        deadline: Optional[str],
    ) -> None:
        response = self.session.get(edit_url, allow_redirects=True)
        self._raise_for_ilias_response(response, "open assignment editor")
        soup = BeautifulSoup(response.text, "html.parser")
        form = self._find_form_with_field(soup, "title", "instruction")
        if form is None or form.find("input", {"name": "cmd[updateAssignment]"}) is None:
            raise ValueError(
                "Could not find the editable assignment form. Check your ILIAS role."
            )

        payload = self._form_payload(form)
        if assignment_title is not None:
            payload = self._set_form_field(payload, "title", assignment_title)
        if instruction is not None:
            payload = self._set_form_field(payload, "instruction", instruction)
        if deadline is not None:
            if deadline:
                payload = self._set_form_field(payload, "deadline_mode", "0")
                payload = self._set_form_field(payload, "deadline", deadline)
                payload = self._set_form_field(payload, "deadline2", deadline)
            else:
                payload = self._set_form_field(payload, "deadline_mode", "-1")
                payload = self._set_form_field(payload, "deadline", "")
                payload = self._set_form_field(payload, "deadline2", "")
        payload = self._set_form_field(
            payload, "cmd[updateAssignment]", "Save"
        )
        action_url = urljoin(response.url, form.get("action", ""))
        result = self.session.post(action_url, data=payload, allow_redirects=True)
        self._raise_for_ilias_response(result, "update assignment")

    def _get_assignment_details(self, edit_url: str, assignment_id: int) -> dict:
        parsed = urlparse(edit_url)
        if parsed.scheme != "https" or parsed.hostname != urlparse(BASE_URL).hostname:
            raise ValueError("ILIAS returned an invalid assignment editor URL.")
        response = self.session.get(edit_url, allow_redirects=True)
        self._raise_for_ilias_response(response, "fetch assignment details")
        soup = BeautifulSoup(response.text, "html.parser")
        form = self._find_form_with_field(soup, "title", "instruction")
        if form is None:
            raise ValueError(f"Could not read assignment {assignment_id}.")

        def value(name: str) -> str:
            field = form.find(attrs={"name": name})
            if field is None:
                return ""
            if field.name == "textarea":
                return field.get_text()
            if field.name == "select":
                selected = field.find("option", selected=True) or field.find("option")
                return selected.get("value", selected.get_text()) if selected else ""
            return field.get("value", "")

        deadline_mode = ""
        for radio in form.find_all("input", {"name": "deadline_mode"}):
            if radio.has_attr("checked"):
                deadline_mode = radio.get("value", "")
                break
        deadline = value("deadline") if deadline_mode == "0" else None
        return {
            "id": assignment_id,
            "title": value("title"),
            "instruction": value("instruction"),
            "deadline": deadline,
            "deadline_mode": deadline_mode,
            "type": value("type"),
            "edit_url": edit_url,
        }

    @staticmethod
    def _find_form_with_field(soup: BeautifulSoup, *field_names: str):
        for form in soup.find_all("form"):
            if all(form.find(attrs={"name": name}) is not None for name in field_names):
                return form
        return None

    @staticmethod
    def _form_payload(form) -> list:
        """Return successful HTML form controls while preserving repeated names."""
        payload = []
        for field in form.find_all(["input", "textarea", "select"]):
            name = field.get("name")
            if not name or field.has_attr("disabled"):
                continue
            field_type = field.get("type", "").lower()
            if field_type in ("submit", "button", "file", "reset", "image"):
                continue
            if field_type in ("checkbox", "radio") and not field.has_attr("checked"):
                continue
            if field.name == "textarea":
                payload.append((name, field.get_text()))
            elif field.name == "select":
                selected = field.find_all("option", selected=True)
                if not selected and not field.has_attr("multiple"):
                    first = field.find("option")
                    selected = [first] if first is not None else []
                payload.extend(
                    (name, option.get("value", option.get_text()))
                    for option in selected
                )
            else:
                payload.append((name, field.get("value", "")))
        return payload

    @staticmethod
    def _set_form_field(payload: list, name: str, value: str) -> list:
        return [(key, item) for key, item in payload if key != name] + [(name, value)]

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(value)).casefold()
        return " ".join(re.findall(r"\w+", normalized, flags=re.UNICODE))

    @staticmethod
    def _search_score(query: str, title: str, searchable: str) -> tuple:
        if query == title:
            return 1000, "exact title"
        if title.startswith(query):
            return 800, "title starts with query"
        if query in title:
            return 650, "title contains query"
        if query in searchable:
            return 450, "item metadata contains query"
        query_tokens = set(query.split())
        searchable_tokens = set(searchable.split())
        overlap = query_tokens & searchable_tokens
        if overlap:
            return int(100 * len(overlap) / len(query_tokens)), "token overlap"
        return 0, "no match"

    @staticmethod
    def _is_exercise_item(item: dict) -> bool:
        return (
            "exercise" in str(item.get("type", "")).casefold()
            or "/goto.php/exc/" in item.get("url", "")
        )

    @staticmethod
    def _exercise_ref_id(url: str) -> int:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != urlparse(BASE_URL).hostname
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "exercise_url must be the exact HTTPS URL returned by "
                "ilias_find_course_items."
            )
        match = re.fullmatch(r"/goto\.php/exc/(\d+)/?", parsed.path)
        if not match:
            raise ValueError(
                "exercise_url must be an ILIAS exercise URL returned by "
                "ilias_find_course_items."
            )
        return int(match.group(1))

    @staticmethod
    def _extract_object_ref_id(url: str) -> Optional[int]:
        ref_id = IliasClient._extract_ref_id(url)
        if ref_id is not None:
            return ref_id
        match = re.search(r"/goto\.php/[a-z]+/(\d+)", urlparse(url).path)
        return int(match.group(1)) if match else None

    @staticmethod
    def _raise_for_ilias_response(response, operation: str) -> None:
        if "login.php" in response.url or "shib_login.php" in response.url:
            raise IliasLoginError(f"Session expired while attempting to {operation}.")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        alert = soup.select_one(".alert-danger, .ilFailureMessage, .error")
        if alert is not None:
            raise ValueError(
                f"Could not {operation}: {alert.get_text(' ', strip=True)}"
            )

    # ------------------------------------------------------------------
    # Publish assignment
    # ------------------------------------------------------------------

    def publish_assignment(
        self,
        course_id: int,
        title: str,
        instruction: str,
        deadline: Optional[str] = None,
        filename: str = "",
        file_content: Optional[bytes] = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Creates an Exercise container and a File Assignment inside it.
        Returns the absolute URL of the new exercise object.
        """
        # Step 1: GET exercise creation page
        init_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={course_id}&cmd=create&new_type=exc"
        )
        res = self.session.get(init_url)

        soup = BeautifulSoup(res.text, "html.parser")
        create_form = None
        for form in soup.find_all("form"):
            if form.find("input", {"name": "cmd[save]"}):
                create_form = form
                break

        if not create_form:
            raise ValueError("Could not find the Exercise creation form on the page.")

        action_url = urljoin(res.url, create_form.get("action", ""))

        # Step 2: Create the Exercise container
        payload = {
            "title": title,
            "desc": f"Exercise container for: {title}",
            "myCounter": "4000",
            "cmd[save]": "Übung anlegen",
        }
        res2 = self.session.post(action_url, data=payload, allow_redirects=True)

        parsed_url = urlparse(res2.url)
        query_params = parse_qs(parsed_url.query)
        new_ref_id_list = query_params.get("ref_id")
        if not new_ref_id_list:
            raise ValueError("Failed to extract new Exercise ref_id from redirect URL.")
        new_ref_id = new_ref_id_list[0]

        # Step 3: GET assignment editor
        editor_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilrepositorygui"
            f"&cmdNode=zl:o6:c1&cmdClass=ilExAssignmentEditorGUI"
            f"&cmd=listAssignments&ref_id={new_ref_id}"
        )
        res_editor = self.session.get(editor_url)

        soup_editor = BeautifulSoup(res_editor.text, "html.parser")
        add_form = None
        for form in soup_editor.find_all("form"):
            if form.find("select", {"name": "type"}):
                add_form = form
                break

        if not add_form:
            raise ValueError(
                "Could not find the addAssignment form on the editor page."
            )

        add_action_url = urljoin(res_editor.url, add_form.get("action", ""))

        # Step 4: Select type=1 (File upload)
        res_details = self.session.post(add_action_url, data={"type": "1"})

        soup_details = BeautifulSoup(res_details.text, "html.parser")
        save_form = None
        for form in soup_details.find_all("form"):
            if form.find("input", {"name": "cmd[saveAssignment]"}):
                save_form = form
                break

        if not save_form:
            raise ValueError(
                "Could not find the saveAssignment form on the details page."
            )

        save_action_url = urljoin(res_details.url, save_form.get("action", ""))

        # Extract hidden inputs
        save_payload: dict = {}
        for inp in save_form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            if name:
                save_payload[name] = inp.get("value", "")

        save_payload.update(
            {
                "title": f"Assignment: {title}",
                "instruction": instruction,
                "myCounter": "4000",
                "mandatory": "1",
                "cmd[saveAssignment]": "Speichern",
            }
        )

        if deadline:
            save_payload.update(
                {
                    "deadline_mode": "0",
                    "start_time": time.strftime("%d.%m.%Y %H:%M"),
                    "deadline": deadline,
                    "deadline2": deadline,
                }
            )
        else:
            save_payload["deadline_mode"] = "-1"

        # Attach file if provided
        if filename and file_content is not None:
            files = {
                "files[0]": (filename, file_content, content_type),
                "fb_file": ("", b"", "application/octet-stream"),
            }
        else:
            files = {
                "files[0]": ("", b"", "application/octet-stream"),
                "fb_file": ("", b"", "application/octet-stream"),
            }

        # Step 5: Save the assignment
        res_final = self.session.post(
            save_action_url, data=save_payload, files=files, allow_redirects=True
        )

        if (
            "editAssignment" not in res_final.url
            and "listAssignments" not in res_final.url
        ):
            soup_final = BeautifulSoup(res_final.text, "html.parser")
            alert = soup_final.find(
                class_=lambda c: (
                    c and any(x in str(c) for x in ["alert-danger", "error"])
                )
            )
            err_msg = (
                alert.get_text(strip=True) if alert else "Unknown validation error"
            )
            raise ValueError(f"Failed to save assignment unit: {err_msg}")

        return f"{BASE_URL}/goto.php/exc/{new_ref_id}"

    # ------------------------------------------------------------------
    # Publish slides (folder + file upload)
    # ------------------------------------------------------------------

    def publish_slides(
        self,
        course_id: int,
        title: str,
        description: str = "",
        files: list = None,
    ) -> str:
        """
        Uploads files to an ILIAS course. Creates a folder when permitted; otherwise
        uploads directly into the course container.
        Returns the URL of the created folder or course.
        ``files`` should be a list of dicts:
            [{"filename": str, "content": bytes, "content_type": str}]
        """
        if files is None:
            files = []

        try:
            parent_ref_id = self._create_folder(course_id, title, description)
            result_url = f"{BASE_URL}/goto.php/fold/{parent_ref_id}"
        except ValueError:
            parent_ref_id = course_id
            result_url = f"{BASE_URL}/goto.php/crs/{course_id}"

        for f in files:
            self._upload_file_to_folder(
                folder_ref_id=parent_ref_id,
                filename=f.get("filename", "file"),
                file_content=f.get("content", b""),
                content_type=f.get("content_type", "application/octet-stream"),
                title=f.get("title", title or f.get("filename", "")),
                description=f.get("description", description),
            )

        return result_url

    def _create_folder(self, parent_ref_id: int, title: str, description: str) -> int:
        init_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={parent_ref_id}&cmd=create&new_type=fold"
        )
        res = self.session.get(init_url)

        soup = BeautifulSoup(res.text, "html.parser")
        create_form = None
        for form in soup.find_all("form"):
            if form.find("input", {"name": "cmd[save]"}):
                create_form = form
                break

        if not create_form:
            raise ValueError("Could not find the Folder creation form.")

        action_url = urljoin(res.url, create_form.get("action", ""))

        payload = {
            "title": title,
            "desc": description,
            "myCounter": "4000",
            "didactic_type": "dtpl_0",
            "cmd[save]": "Ordner anlegen",
        }

        res2 = self.session.post(action_url, data=payload, allow_redirects=True)

        parsed_url = urlparse(res2.url)
        query_params = parse_qs(parsed_url.query)
        new_ref_id_list = query_params.get("ref_id")
        if not new_ref_id_list:
            raise ValueError("Failed to extract new Folder ref_id from redirect URL.")

        return int(new_ref_id_list[0])

    def _upload_file_to_folder(
        self,
        folder_ref_id: int,
        filename: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
        title: str = "",
        description: str = "",
    ) -> str:
        init_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={folder_ref_id}&cmd=create&new_type=file"
        )
        res = self.session.get(init_url)

        soup = BeautifulSoup(res.text, "html.parser")

        # Extract rtoken from form action URLs
        rtoken = None
        for form in soup.find_all("form"):
            action = form.get("action", "")
            if "rtoken=" in action:
                m = re.search(r"rtoken=([a-f0-9]+)", action)
                if m:
                    rtoken = m.group(1)
                    break

        if not rtoken:
            m = re.search(r"rtoken=([a-f0-9]+)", res.text)
            if m:
                rtoken = m.group(1)

        if not rtoken:
            raise ValueError("Could not extract rtoken for file upload.")

        # Step 1: Async binary upload
        ajax_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilrepositorygui"
            f"&cmdNode=zl:of:oj&cmdClass=ilObjFileUploadHandlerGUI"
            f"&cmd=upload&ref_id={folder_ref_id}&new_type=file"
            f"&origin=standard&cmdMode=asynch"
        )
        upload_files = {"file": (filename, file_content, content_type)}
        res_ajax = self.session.post(ajax_url, files=upload_files)
        res_ajax.raise_for_status()

        # Extract temporary file UUID
        file_id = None
        try:
            data = res_ajax.json()
            if isinstance(data, list) and data:
                file_id = data[0].get("id")
            elif isinstance(data, dict):
                file_id = data.get("id") or data.get("file_id")
                if not file_id:
                    for val in data.values():
                        if isinstance(val, str) and re.match(r"^[a-f0-9\-]{36}$", val):
                            file_id = val
                            break
        except Exception:
            pass

        if not file_id:
            m_uuid = re.search(
                r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
                res_ajax.text,
            )
            if m_uuid:
                file_id = m_uuid.group(0)

        if not file_id:
            raise ValueError(
                f"Failed to extract temporary file ID. Response: {res_ajax.text[:200]}"
            )

        # Step 2: Commit file metadata
        save_action_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilrepositorygui"
            f"&cmdNode=zl:of&cmdClass=ilObjFileGUI&cmd=post"
            f"&fallbackCmd=uploadFiles&ref_id={folder_ref_id}"
            f"&new_type=file&origin=standard&rtoken={rtoken}"
        )

        save_payload = {
            "form/input_0[input_1][]": title or filename,
            "form/input_0[input_2][]": description,
            "form/input_0[input_3][]": file_id,
            "form/input_1": "7",
        }

        res_final = self.session.post(
            save_action_url, data=save_payload, allow_redirects=True
        )

        if (
            "cmdClass=ilobjfilegui" not in res_final.url.lower()
            and "cmdClass=ilobjfoldergui" not in res_final.url.lower()
            and res_final.status_code != 200
        ):
            raise ValueError("Failed to save folder file metadata.")

        return f"{BASE_URL}/goto.php/fold/{folder_ref_id}"

    # ------------------------------------------------------------------
    # Publish announcement
    # ------------------------------------------------------------------

    def publish_announcement(
        self,
        course_id: int,
        title: str,
        content: str,
        visibility: str = "users",
    ) -> str:
        """
        Publishes a news/announcement entry to the course timeline.
        Returns the URL of the course timeline.
        """
        try:
            self._enable_news_if_disabled(course_id)
        except Exception as exc:
            # Non-fatal; proceed anyway
            pass

        init_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={course_id}&cmdNode=zl:nn"
            f"&cmdClass=ilNewsTimelineGUI&cmd=show"
        )
        res = self.session.get(init_url)
        soup = BeautifulSoup(res.text, "html.parser")

        news_form = None
        for form in soup.find_all("form"):
            if "ilNewsTimelineGUI" in form.get("action", ""):
                news_form = form
                break

        if not news_form:
            raise ValueError("Could not find the news timeline edit form on the page.")

        action_url = urljoin(res.url, news_form.get("action", ""))

        payload: dict = {}
        for inp in news_form.find_all("input", {"type": "hidden"}):
            name = inp.get("name")
            if name:
                payload[name] = inp.get("value", "")

        payload.update(
            {
                "news_title": title,
                "news_content": content,
                "news_visibility": visibility
                if visibility in ("users", "public")
                else "users",
                "news_action": "save",
                "cmd[updateNewsItem]": "Speichern",
            }
        )

        media_files = {"media": ("", b"", "application/octet-stream")}
        res_final = self.session.post(
            action_url, data=payload, files=media_files, allow_redirects=True
        )

        if "error.php" in res_final.url:
            soup_err = BeautifulSoup(res_final.text, "html.parser")
            alert = soup_err.find(class_=lambda c: c and "alert" in str(c))
            err_text = alert.get_text(strip=True) if alert else "Unknown server error"
            raise ValueError(
                f"Failed to publish announcement (server error): {err_text}"
            )

        soup_final = BeautifulSoup(res_final.text, "html.parser")
        alert_danger = soup_final.find(class_=lambda c: c and "alert-danger" in str(c))
        if alert_danger:
            raise ValueError(
                f"Failed to publish announcement: {alert_danger.get_text(strip=True)}"
            )

        return (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={course_id}&cmdNode=zl:nn"
            f"&cmdClass=ilNewsTimelineGUI&cmd=show"
        )

    def _enable_news_if_disabled(self, course_ref_id: int):
        """Ensures news/announcements are enabled in course settings."""
        settings_url = (
            f"{BASE_URL}/ilias.php?baseClass=ilRepositoryGUI"
            f"&ref_id={course_ref_id}&cmdClass=ilnewsitemgui&cmd=edit"
        )
        res = self.session.get(settings_url)
        soup = BeautifulSoup(res.text, "html.parser")

        inp_news = soup.find("input", {"name": "cont_use_news"})
        if inp_news and inp_news.has_attr("checked"):
            return

        forms = soup.find_all("form")
        settings_form = None
        if len(forms) > 2:
            settings_form = forms[2]
        else:
            for form in forms:
                if form.find("input", {"name": "cont_use_news"}):
                    settings_form = form
                    break

        if not settings_form:
            return

        action_url = urljoin(res.url, settings_form.get("action", ""))

        payload: dict = {}
        for inp in settings_form.find_all(["input", "textarea", "select"]):
            name = inp.get("name")
            if not name:
                continue
            inp_type = inp.get("type")
            if inp_type in ("checkbox", "radio"):
                if inp.has_attr("checked") or name == "cont_use_news":
                    payload[name] = (
                        "1" if name == "cont_use_news" else inp.get("value", "1")
                    )
            elif inp.name == "select":
                selected = inp.find("option", selected=True)
                if selected:
                    payload[name] = selected.get("value", "")
                else:
                    options = inp.find_all("option")
                    if options:
                        payload[name] = options[0].get("value", "")
            else:
                payload[name] = inp.get("value", "")

        payload["cmd[update]"] = "Speichern"
        self.session.post(action_url, data=payload, allow_redirects=True)

    # ------------------------------------------------------------------
    # File download
    # ------------------------------------------------------------------

    def download_file(self, url: str) -> bytes:
        """
        Download a file from the given ILIAS URL using the current session cookies.
        Returns the raw bytes content.
        """
        res = self.session.get(url, allow_redirects=True)
        if "login.php" in res.url or "shib_login.php" in res.url:
            raise IliasLoginError("Session expired while downloading file.")
        res.raise_for_status()
        return res.content

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_ref_id(url: str) -> Optional[int]:
        """Extract ``ref_id`` query parameter from a URL, or None."""
        try:
            params = parse_qs(urlparse(url).query)
            ref_list = params.get("ref_id")
            if ref_list:
                return int(ref_list[0])
        except (ValueError, TypeError):
            pass
        return None
