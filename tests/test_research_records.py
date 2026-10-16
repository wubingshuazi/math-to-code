"""A repeated research command must preserve the original experiment."""

from argparse import Namespace
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import scipy
    import numpy
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from search_thermal import run
    HAS_SEARCH = True
except ImportError:
    HAS_SEARCH = False


@unittest.skipUnless(HAS_SEARCH, "optional search dependencies are unavailable")
class ResearchRecordTests(unittest.TestCase):
    def test_existing_result_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "search.json"
            destination.write_bytes(b'{"previous_result": true}\n')
            original = destination.read_bytes()
            args = Namespace(output=destination, seconds=1, seed=1,
                             starts=1, max_evals=10, workers=1)
            with self.assertRaises(FileExistsError):
                run(args)
            self.assertEqual(destination.read_bytes(), original)
            self.assertFalse((destination.parent / "sharpness_journals").exists())

    def test_existing_worker_journal_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "search.json"
            journal_directory = destination.parent / "sharpness_journals"
            journal_directory.mkdir()
            journal = journal_directory / "start_000.jsonl"
            journal.write_bytes(b'{"event": "previous_witness"}\n')
            args = Namespace(output=destination, seconds=1, seed=1,
                             starts=1, max_evals=10, workers=1)
            with self.assertRaises(FileExistsError):
                run(args)
            self.assertEqual(journal.read_bytes(), b'{"event": "previous_witness"}\n')
            self.assertFalse(destination.exists())
