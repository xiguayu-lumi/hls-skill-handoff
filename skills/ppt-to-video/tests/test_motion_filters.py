import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "ppt_to_video.py"
SPEC = importlib.util.spec_from_file_location("ppt_to_video", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MotionFilterTests(unittest.TestCase):
    def test_subtle_motion_adds_gentle_zoom_and_fade_in(self):
        filter_graph = MODULE.build_motion_filter("subtle", fps=25)

        self.assertIn("zoompan=", filter_graph)
        self.assertIn("1.04", filter_graph)
        self.assertIn("fade=t=in:st=0:d=0.35", filter_graph)
        self.assertIn("fps=25", filter_graph)

    def test_none_motion_keeps_only_standard_fit_filter(self):
        filter_graph = MODULE.build_motion_filter("none", fps=25)

        self.assertNotIn("zoompan=", filter_graph)
        self.assertNotIn("fade=t=in", filter_graph)
        self.assertIn("fps=25", filter_graph)


if __name__ == "__main__":
    unittest.main()
