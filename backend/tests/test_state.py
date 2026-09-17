import os
import stat
import tempfile
import unittest
import fcntl
import multiprocessing
from pathlib import Path

from state import StateCorruptionError, StateStore


def _try_nonblocking_lock(path, result):
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result.put(True)
        except BlockingIOError:
            result.put(False)
    finally:
        os.close(descriptor)


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "credentials" / "ilias-state.json"
        self.store = StateStore(self.path)

    def tearDown(self):
        self.temporary.cleanup()

    def test_creates_owner_only_state_and_lock(self):
        with self.store.locked():
            self.store.save(self.store.empty())
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.path.parent).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(self.store.lock_path).st_mode), 0o600)

    def test_atomic_save_replaces_valid_json(self):
        state = self.store.empty()
        state["phpsessid"] = "new-session"
        with self.store.locked():
            self.store.save(state)
            loaded = self.store.load()
        self.assertEqual(loaded["phpsessid"], "new-session")
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_corrupt_state_is_preserved_for_repair(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("not-json", encoding="utf-8")
        with self.assertRaises(StateCorruptionError):
            self.store.load()
        backups = list(self.path.parent.glob("ilias-state.json.corrupt-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "not-json")

    def test_lock_rejects_concurrent_writer(self):
        result = multiprocessing.Queue()
        with self.store.locked():
            child = multiprocessing.Process(
                target=_try_nonblocking_lock, args=(str(self.store.lock_path), result)
            )
            child.start()
            child.join()
        self.assertFalse(result.get(timeout=1))
