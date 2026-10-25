"""Compiler path handling and diagnostics, independent of the disk cache."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from manimlib.utils import tex_file_writing as tex


class TexFileWritingTests(unittest.TestCase):
    def test_compiler_uses_basename_in_cache_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary) / "USER~1 with spaces" / "latex"
            with patch.dict(tex.manim_config.directories, {"latex_cache": str(cache)}), \
                 patch.object(tex.subprocess, "run", side_effect=[
                     subprocess.CompletedProcess([], 0, "", ""),
                     subprocess.CompletedProcess([], 0, b"<svg/>", b""),
                 ]) as run:
                self.assertEqual(tex.full_tex_to_svg.__wrapped__("test"), "<svg/>")
            self.assertEqual(run.call_args_list[0].args[0][-1], "working.tex")
            self.assertEqual(run.call_args_list[0].kwargs["cwd"], cache)
            self.assertEqual((cache / "working.tex").read_text(), "test")

    def test_failed_compilation_rejects_stale_dvi_and_reports_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary)
            (cache / "working.dvi").write_bytes(b"stale")
            (cache / "working.log").write_text("! Emergency stop.\n<to be read again>\n")
            with patch.dict(tex.manim_config.directories, {"latex_cache": str(cache)}), \
                 patch.object(tex.subprocess, "run", return_value=
                              subprocess.CompletedProcess([], 1, "", "")) as run:
                with self.assertRaisesRegex(tex.LatexError, "Emergency stop"):
                    tex.full_tex_to_svg.__wrapped__("invalid")
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

