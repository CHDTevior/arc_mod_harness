import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("projection",ROOT/"skills/arc-mod-harness/scripts/project_points.py")
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class ProjectionTests(unittest.TestCase):
    def setUp(self):self.d=json.loads((ROOT/"examples/projection-input.json").read_text())
    def test_known_coordinates(self):
        r=p.project(self.d);self.assertEqual(r["points"][0]["pixel"],[120,324]);self.assertEqual(r["points"][0]["normalized"],[.125,.6])
    def test_row_major_translation(self):
        self.d["world_to_clip"][0][3]=.1
        self.assertAlmostEqual(p.project(self.d)["points"][0]["pixel"][0],168)
    def test_perspective_divide(self):
        self.d["world_to_clip"][3][3]=2
        self.assertEqual(p.project(self.d)["points"][0]["normalized"],[.3125,.55])
    def test_behind_camera_not_projected(self):
        self.d["world_to_clip"][3][3]=-1
        self.assertIsNone(p.project(self.d)["points"][0]["pixel"])
    def test_unknown_visibility_is_explicit(self):
        del self.d["points"][0]["visible"]
        self.assertEqual(p.project(self.d)["points"][0]["visible"],"unknown")
    def test_no_automatic_edges(self):
        self.d["edges"]=[]
        self.assertEqual(p.project(self.d)["edges"],[])
    def test_bad_edge(self):
        self.d["edges"]=[["missing","R.pupil"]]
        with self.assertRaises(ValueError):p.project(self.d)
    def test_nonfinite_rejected(self):
        self.d["world_to_clip"][0][0]=float("nan")
        with self.assertRaises(ValueError):p.project(self.d)
    def test_duplicate_ID_rejected(self):
        self.d["points"].append(copy.deepcopy(self.d["points"][0]))
        with self.assertRaises(ValueError):p.project(self.d)
    def test_convention_required(self):
        del self.d["matrix_convention"]
        with self.assertRaises(ValueError):p.project(self.d)
    def test_offscreen_retained_but_not_drawn(self):
        self.d["points"][0]["world"]=[5,0,0]
        self.assertEqual(p.project(self.d)["points"][0]["clip_status"],"outside")
    def test_labels_are_escaped(self):
        self.d["camera"]="<script>"
        s=p.svg(p.project(self.d));self.assertIn("&lt;script&gt;",s);self.assertNotIn("<script>",s)


if __name__=="__main__":unittest.main()
