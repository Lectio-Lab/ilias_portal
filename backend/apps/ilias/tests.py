from unittest.mock import MagicMock

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from .client import IliasClient
from .serializers import EditExerciseSerializer


class FakeResponse:
    def __init__(self, html: str, url: str = "https://ovidius.uni-tuebingen.de/ilias.php"):
        self.text = html
        self.url = url
        self.status_code = 200

    def raise_for_status(self):
        return None


class CourseItemSearchTests(SimpleTestCase):
    def setUp(self):
        self.client = IliasClient("", "")
        self.client.get_course_contents = MagicMock(
            return_value={
                "course_title": "Machine Learning",
                "sections": [
                    {
                        "section": "Exercises",
                        "items": [
                            {
                                "title": "CNN Homework",
                                "url": "https://ovidius.uni-tuebingen.de/goto.php/exc/123",
                                "type": "Exercise",
                                "properties": {},
                            },
                            {
                                "title": "CNN Lecture Notes",
                                "url": "https://ovidius.uni-tuebingen.de/goto.php/file/456",
                                "type": "File",
                                "properties": {},
                            },
                        ],
                    }
                ],
            }
        )
        self.client.get_exercise_details = MagicMock(
            return_value={"title": "CNN Homework", "assignments": []}
        )

    def test_find_ranks_exact_title_and_returns_url_and_content(self):
        result = self.client.find_course_items(99, "CNN Homework")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matches"][0]["match_reason"], "exact title")
        self.assertEqual(
            result["matches"][0]["url"],
            "https://ovidius.uni-tuebingen.de/goto.php/exc/123",
        )
        self.assertEqual(result["matches"][0]["content"]["title"], "CNN Homework")

    def test_find_applies_type_filter(self):
        result = self.client.find_course_items(99, "CNN", item_type="Exercise")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["matches"][0]["type"], "Exercise")


class ExerciseEditTests(SimpleTestCase):
    exercise_url = "https://ovidius.uni-tuebingen.de/goto.php/exc/123"

    def setUp(self):
        self.client = IliasClient("", "")
        self.client.get_course_contents = MagicMock(
            return_value={
                "sections": [
                    {
                        "section": "Exercises",
                        "items": [
                            {
                                "title": "CNN Homework",
                                "url": self.exercise_url,
                                "type": "Exercise",
                                "properties": {},
                            }
                        ],
                    }
                ]
            }
        )
        self.before = {
            "ref_id": 123,
            "title": "CNN Homework",
            "description": "Old description",
            "url": self.exercise_url,
            "editable": True,
            "assignments": [
                {
                    "id": 7,
                    "title": "Assignment: CNN Homework",
                    "instruction": "Old instructions",
                    "deadline": "20.08.2026 23:59",
                    "deadline_mode": "0",
                    "type": "1",
                    "edit_url": "https://ovidius.uni-tuebingen.de/ilias.php?cmd=editAssignment&ass_id=7",
                }
            ],
        }
        self.after = {
            **self.before,
            "assignments": [
                {
                    **self.before["assignments"][0],
                    "instruction": "New instructions",
                    "deadline": None,
                    "deadline_mode": "-1",
                }
            ],
        }
        self.client.get_exercise_details = MagicMock(
            side_effect=[self.before, self.after]
        )
        self.client._update_assignment = MagicMock()
        self.client._update_exercise_settings = MagicMock()

    def test_edits_single_assignment_and_verifies_result(self):
        result = self.client.edit_exercise(
            course_id=99,
            exercise_url=self.exercise_url,
            expected_title="CNN Homework",
            expected_instruction="Old instructions",
            expected_deadline="20.08.2026 23:59",
            instruction="New instructions",
            deadline="",
        )

        self.assertTrue(result["verified"])
        self.assertEqual(result["url"], self.exercise_url)
        self.assertEqual(result["assignment"]["instruction"], "New instructions")
        self.client._update_assignment.assert_called_once_with(
            self.before["assignments"][0]["edit_url"],
            assignment_title=None,
            instruction="New instructions",
            deadline="",
        )
        self.client._update_exercise_settings.assert_not_called()

    def test_rejects_stale_instruction_before_writing(self):
        with self.assertRaisesRegex(ValueError, "instruction changed since discovery"):
            self.client.edit_exercise(
                course_id=99,
                exercise_url=self.exercise_url,
                expected_title="CNN Homework",
                expected_instruction="Older instructions",
                instruction="New instructions",
            )

        self.client._update_assignment.assert_not_called()

    def test_rejects_stale_expected_title_before_writing(self):
        with self.assertRaisesRegex(ValueError, "title changed or does not match"):
            self.client.edit_exercise(
                course_id=99,
                exercise_url=self.exercise_url,
                expected_title="A different exercise",
                instruction="New instructions",
            )

        self.client._update_assignment.assert_not_called()
        self.client._update_exercise_settings.assert_not_called()

    def test_rejects_url_not_present_in_course_before_writing(self):
        with self.assertRaisesRegex(ValueError, "not an exercise in the requested course"):
            self.client.edit_exercise(
                course_id=99,
                exercise_url="https://ovidius.uni-tuebingen.de/goto.php/exc/999",
                expected_title="Other",
                instruction="New instructions",
            )

        self.client._update_assignment.assert_not_called()

    def test_rejects_multiple_assignments_without_assignment_id(self):
        second = {**self.before["assignments"][0], "id": 8, "title": "Part 2"}
        self.before["assignments"].append(second)
        self.client.get_exercise_details = MagicMock(return_value=self.before)

        with self.assertRaisesRegex(ValueError, "multiple assignment units"):
            self.client.edit_exercise(
                course_id=99,
                exercise_url=self.exercise_url,
                expected_title="CNN Homework",
                instruction="New instructions",
            )

        self.client._update_assignment.assert_not_called()

    def test_rejects_noncanonical_or_external_exercise_url(self):
        invalid_urls = [
            "https://evil.example/goto.php/exc/123",
            "http://ovidius.uni-tuebingen.de/goto.php/exc/123",
            "https://ovidius.uni-tuebingen.de/goto.php/exc/123?other=1",
        ]
        for url in invalid_urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.client._exercise_ref_id(url)


class HtmlFormTests(SimpleTestCase):
    def test_form_payload_preserves_checked_and_selected_values(self):
        soup = BeautifulSoup(
            """
            <form>
              <input type="text" name="title" value="Old">
              <textarea name="instruction">Old text</textarea>
              <input type="checkbox" name="mandatory" value="1" checked>
              <input type="checkbox" name="ignored" value="1">
              <input type="file" name="attachment">
              <select name="type"><option value="1" selected>Upload</option></select>
              <input type="submit" name="cmd[updateAssignment]" value="Save">
            </form>
            """,
            "html.parser",
        )

        payload = IliasClient._form_payload(soup.form)

        self.assertIn(("title", "Old"), payload)
        self.assertIn(("instruction", "Old text"), payload)
        self.assertIn(("mandatory", "1"), payload)
        self.assertIn(("type", "1"), payload)
        self.assertNotIn(("ignored", "1"), payload)
        self.assertFalse(any(name == "attachment" for name, _ in payload))
        self.assertFalse(any(name == "cmd[updateAssignment]" for name, _ in payload))

    def test_assignment_update_replaces_content_and_removes_deadline(self):
        edit_url = (
            "https://ovidius.uni-tuebingen.de/ilias.php"
            "?cmd=editAssignment&ass_id=7"
        )
        form_html = """
        <form action="/ilias.php?cmd=post">
          <input type="text" name="title" value="Old title">
          <textarea name="instruction">Old instructions</textarea>
          <input type="radio" name="deadline_mode" value="0" checked>
          <input type="text" name="deadline" value="20.08.2026 23:59">
          <input type="text" name="deadline2" value="20.08.2026 23:59">
          <input type="submit" name="cmd[updateAssignment]" value="Save">
        </form>
        """
        client = IliasClient("", "")
        client.session = MagicMock()
        client.session.get.return_value = FakeResponse(form_html, edit_url)
        client.session.post.return_value = FakeResponse("<div>Saved</div>", edit_url)

        client._update_assignment(
            edit_url,
            assignment_title=None,
            instruction="New instructions",
            deadline="",
        )

        posted = dict(client.session.post.call_args.kwargs["data"])
        self.assertEqual(posted["instruction"], "New instructions")
        self.assertEqual(posted["deadline_mode"], "-1")
        self.assertEqual(posted["deadline"], "")
        self.assertEqual(posted["deadline2"], "")
        self.assertEqual(posted["cmd[updateAssignment]"], "Save")


class EditExerciseSerializerTests(SimpleTestCase):
    def test_requires_current_value_for_each_replacement(self):
        serializer = EditExerciseSerializer(
            data={
                "exercise_url": "https://ovidius.uni-tuebingen.de/goto.php/exc/123",
                "expected_title": "CNN Homework",
                "instruction": "New instructions",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("expected_instruction", str(serializer.errors))

    def test_rejects_malformed_deadline(self):
        serializer = EditExerciseSerializer(
            data={
                "exercise_url": "https://ovidius.uni-tuebingen.de/goto.php/exc/123",
                "expected_title": "CNN Homework",
                "expected_deadline": None,
                "deadline": "tomorrow",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("DD.MM.YYYY HH:MM", str(serializer.errors))
