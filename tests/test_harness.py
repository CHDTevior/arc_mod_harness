import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/arc-mod-harness/scripts/harness.py"
spec = importlib.util.spec_from_file_location("harness", SCRIPT)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        h.run(h.make_parser().parse_args(["init", str(self.root), "--name", "测试项目"]))
        self.s = h.load(self.root)
        self.s["answers"] = {"scopes": {"value": ["face"], "status": "answer"}, "game_build": {"value": "demo-build", "status": "answer"}}

    def add(self, ident="a", kind="source", stage="motion", role="source", variant="shared", deps=None, built=None, meta=None, suffix=".txt"):
        p = self.root / "source" / (ident + suffix)
        p.write_text(ident, encoding="utf-8")
        h.register(self.root, self.s, ident, "source/" + p.name, kind, stage, role, variant, deps, built, meta)
        return p

    def capture(self, ident="capture", kind="engine_capture", stage="motion", built=None):
        return self.add(ident, kind, stage, "evidence", built=built, meta={"camera":"native", "source_camera":True,"reviewed_frames":[0,1,2],"game_build":"demo-build", "environment":"test PC"}, suffix=".png")

    def motion_decision(self):
        self.capture()
        self.add("projection", "projection", role="evidence")
        return h.review(self.root, self.s, "motion", ["capture", "projection"], "accept", "喜欢这个", "synthetic-test")

    def test_init_never_overwrites(self):
        with self.assertRaises(h.HarnessError): h.run(h.make_parser().parse_args(["init", str(self.root), "--name", "bad"]))

    def test_voice_route_skips_body(self):
        self.s["answers"]["scopes"]["value"] = ["voice"]
        self.assertNotIn("base", h.route(self.s)); self.assertNotIn("rig", h.route(self.s)); self.assertIn("voice", h.route(self.s))
        self.assertNotIn("base_source", [q["id"] for q in h.eligible_questions(self.s)])

    def test_pending_is_not_accepted(self):
        report = h.inspect(self.root, self.s, "share")
        self.assertTrue(report["errors"]); self.assertEqual(report["stages"]["runtime"], "pending")

    def test_changed_file_invalidates_decision(self):
        d = self.motion_decision()
        self.assertTrue(h.decision_current(self.root, self.s, d))
        (self.root / "source/capture.png").write_text("changed")
        self.assertFalse(h.decision_current(self.root, self.s, d))

    def test_changed_dependency_invalidates_decision(self):
        p = self.add("mesh")
        self.capture(built=["mesh"]); self.add("projection", "projection", role="evidence")
        d = h.review(self.root, self.s, "motion", ["capture", "projection"], "accept", "yes", "test")
        p.write_text("changed")
        self.assertFalse(h.decision_current(self.root, self.s, d))

    def test_changed_camera_invalidates_decision(self):
        d = self.motion_decision(); self.s["artifacts"]["capture"]["metadata"]["camera"] = "other"
        self.assertFalse(h.decision_current(self.root, self.s, d))

    def test_changed_variant_invalidates_decision(self):
        d = self.motion_decision(); self.s["selected_variant"] = "C"
        self.assertFalse(h.decision_current(self.root, self.s, d))

    def test_changed_answer_invalidates_decision(self):
        d = self.motion_decision(); self.s["answers"]["intent"] = {"value":"new"}
        self.assertFalse(h.decision_current(self.root, self.s, d))

    def test_no_faked_runtime_from_engine(self):
        self.capture(kind="engine_capture", stage="runtime")
        with self.assertRaisesRegex(h.HarnessError, "game_capture"):
            h.review(self.root, self.s, "runtime", ["capture"], "accept", "yes", "test")

    def test_concept_cannot_pass_motion(self):
        self.add("ai", "concept", role="reference")
        with self.assertRaises(h.HarnessError): h.review(self.root, self.s, "motion", ["ai"], "accept", "yes", "test")

    def test_motion_needs_projection_and_coverage(self):
        self.capture()
        with self.assertRaisesRegex(h.HarnessError, "projection"): h.review(self.root, self.s, "motion", ["capture"], "accept", "yes", "test")
        self.add("p", "projection", role="evidence")
        self.s["artifacts"]["capture"]["metadata"]["reviewed_frames"] = []
        with self.assertRaisesRegex(h.HarnessError, "reviewed_frames"): h.review(self.root, self.s, "motion", ["capture", "p"], "accept", "yes", "test")

    def test_runtime_requires_package_lineage(self):
        self.capture(kind="game_capture", stage="runtime")
        with self.assertRaisesRegex(h.HarnessError, "package report"): h.review(self.root, self.s, "runtime", ["capture"], "accept", "yes", "test")

    def test_runtime_with_package_lineage(self):
        self.add("pak-report", "package_report", "package", "evidence")
        self.capture(kind="game_capture", stage="runtime", built=["pak-report"])
        d = h.review(self.root, self.s, "runtime", ["capture"], "accept", "tested this scene", "test")
        self.assertTrue(h.decision_current(self.root, self.s, d))

    def test_base_requires_three_views(self):
        self.s["answers"]["scopes"]["value"] = ["body"]
        self.add("front", "dcc_capture", "base", "evidence", meta={"camera":"front", "views":["front"]})
        self.add("audit", "technical_report", "base", "evidence")
        with self.assertRaisesRegex(h.HarnessError, "front/side/back"): h.review(self.root, self.s, "base", ["front","audit"], "accept", "yes", "test")

    def test_open_feedback_prevents_accept(self):
        self.capture(); self.add("p", "projection", role="evidence")
        self.s["feedback"].append({"id":"f", "artifact":"capture", "status":"open"})
        with self.assertRaisesRegex(h.HarnessError, "feedback"): h.review(self.root, self.s, "motion", ["capture","p"], "accept", "yes", "test")

    def test_quote_cannot_be_empty(self):
        self.capture()
        with self.assertRaises(h.HarnessError): h.review(self.root, self.s, "motion", ["capture"], "defer", "", "test")

    def test_traversal_and_windows_paths_denied(self):
        for path in ("../secret", "/outside", "C:/outside", "sub/../../x", "sub\\x", "x//y", "x/./y"):
            with self.subTest(path=path), self.assertRaises(h.HarnessError): h.local_path(self.root, path)

    def test_missing_dependency_denied(self):
        with self.assertRaisesRegex(h.HarnessError, "Missing"): self.add(deps=["missing"])

    def test_cycle_denied(self):
        self.add("a"); self.add("b", deps=["a"]); self.s["artifacts"]["a"]["dependencies"]=["b"]
        with self.assertRaisesRegex(h.HarnessError, "cycle"): h.closure(self.s, ["a"])

    def runtime(self, ident, variant="C", deps=None, mount=None):
        return self.add(ident, "runtime_file", "package", "runtime", variant, deps, meta={"package_path": mount or f"Game/{ident}.asset"})

    def test_selected_C_excludes_AB(self):
        for v in ("A","B","C"): self.runtime(v, v)
        self.s["selected_variant"] = "C"
        plan = h.release_plan(self.root, self.s)
        self.assertEqual([f["id"] for f in plan["files"]], ["C"])
        self.assertIn("A", plan["excluded"]); self.assertIn("B", plan["excluded"])

    def test_cross_variant_runtime_dependency_denied(self):
        self.runtime("B", "B"); self.runtime("C", deps=["B"]); self.s["selected_variant"]="C"
        with self.assertRaisesRegex(h.HarnessError, "unselected"): h.release_plan(self.root,self.s)

    def test_unbundled_dependency_denied(self):
        self.add("third-party"); self.runtime("C",deps=["third-party"]); self.s["selected_variant"]="C"
        with self.assertRaisesRegex(h.HarnessError, "Unbundled"): h.release_plan(self.root,self.s)

    def test_stock_dependency_build_checked(self):
        self.add("stock", "stock_dependency", "package", "stock", meta={"game_build":"wrong"})
        self.runtime("C",deps=["stock"]); self.s["selected_variant"]="C"
        with self.assertRaisesRegex(h.HarnessError, "game-build"): h.release_plan(self.root,self.s)
        self.s["artifacts"]["stock"]["metadata"]["game_build"]="demo-build"
        self.assertEqual(h.release_plan(self.root,self.s)["stock_dependencies"],["stock"])

    def test_duplicate_mount_casefold_denied(self):
        self.runtime("C1",mount="Game/Face.asset"); self.runtime("C2",mount="game/face.asset"); self.s["selected_variant"]="C"
        with self.assertRaisesRegex(h.HarnessError, "Duplicate"): h.release_plan(self.root,self.s)

    def test_clean_plan_protects_provenance(self):
        self.add("temp-used",role="temporary"); self.add("temp-unused",role="temporary"); self.add("source",built=["temp-used"])
        plan=h.clean_plan(self.root,self.s)
        self.assertEqual([f["id"] for f in plan["files"]],["temp-unused"])
        self.assertTrue((self.root/"source/temp-unused.txt").exists())

    def test_clean_plan_protects_reviewed_and_archived(self):
        self.add("old","reference","reference","temporary")
        h.review(self.root,self.s,"reference",["old"],"revise","no","test")
        self.add("archive",role="archive")
        self.assertEqual(h.clean_plan(self.root,self.s)["files"],[])

    def test_clean_plan_rejects_changed_temp(self):
        p=self.add("temp",role="temporary");p.write_text("changed")
        with self.assertRaises(h.HarnessError):h.clean_plan(self.root,self.s)

    def test_cleanup_same_path_cannot_bypass_protection(self):
        self.add("source")
        h.register(self.root,self.s,"alias","source/source.txt","source","motion","temporary")
        self.assertEqual(h.clean_plan(self.root,self.s)["files"],[])

    def test_symlink_denied_if_available(self):
        outside=Path(self.tmp.name)/"outside";outside.mkdir()
        try:(self.root/"linked").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("symlinks unavailable")
        with self.assertRaises(h.HarnessError):h.local_path(self.root,"linked/file")

    def test_review_page_escapes_metadata_and_labels_AI(self):
        self.add("ai","concept","reference","reference",meta={"camera":"<script>evil</script>"},suffix=".svg")
        out=h.review_pack(self.root,self.s,["ai"],"reviews/test")
        text=Path(out["page"]).read_text(encoding="utf-8")
        self.assertIn("AI 概念参考",text);self.assertIn("&lt;script&gt;evil",text);self.assertNotIn("<script>evil",text)
        self.assertTrue((self.root/"reviews/test/media/ai.svg").exists())

    def test_cli_error_is_structured_nonzero(self):
        h.save(self.root,self.s)
        result=subprocess.run([sys.executable,str(SCRIPT),"add",str(self.root),"bad","../bad","--kind","source","--stage","base"],capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(result.returncode,2);self.assertIn("error",json.loads(result.stderr))

    def test_retire_preserves_file(self):
        p=self.runtime("old");h.save(self.root,self.s)
        h.run(h.make_parser().parse_args(["retire",str(self.root),"old","--note","superseded"]))
        self.assertTrue(p.exists());self.assertEqual(h.load(self.root)["artifacts"]["old"]["role"],"archive")

    def test_new_package_invalidates_old_runtime_evidence(self):
        self.runtime("runtime",variant="main")
        self.add("pkg1","package_report","package","evidence",built=["runtime"])
        h.review(self.root,self.s,"package",["pkg1"],"accept","checked","test")
        self.capture(kind="game_capture",stage="runtime",built=["pkg1"])
        h.review(self.root,self.s,"runtime",["capture"],"accept","checked","test")
        self.assertEqual(h.inspect(self.root,self.s)["stages"]["runtime"],"accept")
        self.add("pkg2","package_report","package","evidence",built=["runtime"])
        h.review(self.root,self.s,"package",["pkg2"],"accept","new package","test")
        self.assertEqual(h.inspect(self.root,self.s)["stages"]["runtime"],"package_mismatch")

    def test_package_cannot_ignore_selected_runtime(self):
        self.runtime("runtime",variant="main")
        self.add("pkg","package_report","package","evidence")
        with self.assertRaisesRegex(h.HarnessError,"all selected runtime"):
            h.review(self.root,self.s,"package",["pkg"],"accept","checked","test")

    def test_complete_material_records_can_qualify_but_are_not_game_execution(self):
        self.s["answers"]["scopes"]["value"]=["material"]
        self.add("brief","brief","brief","evidence")
        h.review(self.root,self.s,"brief",["brief"],"accept","brief yes","fixture")
        self.add("reference","reference","reference","reference")
        h.review(self.root,self.s,"reference",["reference"],"accept","reference yes","fixture")
        self.capture("look",stage="look");self.add("look-report","technical_report","look","evidence")
        h.review(self.root,self.s,"look",["look","look-report"],"accept","look yes","fixture")
        self.capture()
        h.review(self.root,self.s,"motion",["capture"],"accept","motion yes","fixture")
        self.runtime("runtime",variant="main")
        self.add("pkg","package_report","package","evidence",built=["runtime"])
        h.review(self.root,self.s,"package",["pkg"],"accept","package yes","fixture")
        self.capture("game",kind="game_capture",stage="runtime",built=["pkg"])
        h.review(self.root,self.s,"runtime",["game"],"accept","runtime yes","fixture")
        self.assertEqual(h.inspect(self.root,self.s,"share")["errors"],[])
        self.assertTrue(h.inspect(self.root,self.s,"friend-verified")["errors"])
        self.capture("friend",kind="friend_capture",stage="delivery",built=["pkg"])
        self.add("delivery-report","package_report","delivery","evidence",built=["pkg"])
        h.review(self.root,self.s,"delivery",["friend","delivery-report"],"accept","friend yes","fixture")
        self.assertEqual(h.inspect(self.root,self.s,"friend-verified")["errors"],[])


if __name__=="__main__":unittest.main()
