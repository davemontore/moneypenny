import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class PackagedReplacementTests(unittest.TestCase):
    def _prepare_tree(self, root: Path):
        source_script = Path(__file__).resolve().parents[1] / "Build MoneyPenny.exe.bat"
        script = root / source_script.name
        shutil.copy2(source_script, script)

        packaged = root / "build" / "packaged-dist" / "MoneyPenny"
        (packaged / "_internal").mkdir(parents=True)
        (packaged / "_internal" / "new-runtime.txt").write_text(
            "new runtime",
            encoding="utf-8",
        )
        (packaged / "MoneyPenny.exe").write_bytes(b"new executable")

        live = root / "dist" / "MoneyPenny"
        (live / "_internal").mkdir(parents=True)
        (live / "_internal" / "old-runtime.txt").write_text(
            "old runtime",
            encoding="utf-8",
        )
        (live / "MoneyPenny.exe").write_bytes(b"old executable")
        (live / "settings.json").write_bytes(b"private settings")
        return script, live

    def test_replacement_preserves_private_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script, live = self._prepare_tree(Path(temp_dir))

            result = subprocess.run(
                ["cmd", "/c", str(script), "--replace-only"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=20,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((live / "MoneyPenny.exe").read_bytes(), b"new executable")
            self.assertTrue((live / "_internal" / "new-runtime.txt").exists())
            self.assertEqual((live / "settings.json").read_bytes(), b"private settings")
            self.assertFalse((live / "_internal.previous").exists())
            self.assertFalse((live / "MoneyPenny.previous.exe").exists())

    def test_locked_executable_restores_previous_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script, live = self._prepare_tree(Path(temp_dir))

            with open(live / "MoneyPenny.exe", "rb") as locked_executable:
                self.assertTrue(locked_executable.read(1))
                result = subprocess.run(
                    ["cmd", "/c", str(script), "--replace-only"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )

            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((live / "MoneyPenny.exe").read_bytes(), b"old executable")
            self.assertTrue((live / "_internal" / "old-runtime.txt").exists())
            self.assertEqual((live / "settings.json").read_bytes(), b"private settings")
            self.assertFalse((live / "_internal.next").exists())
            self.assertFalse((live / "_internal.previous").exists())


if __name__ == "__main__":
    unittest.main()
