import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "skills/arc-mod-harness/examples/cook_install_demo.py"
SPEC = importlib.util.spec_from_file_location("cook_install_demo", SOURCE)
demo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(demo)


class CookInstallExampleTests(unittest.TestCase):
    def test_all_extracted_companions_and_extra_files_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("mesh.uasset", "mesh.uexp", "mesh.ubulk"):
                (root / name).write_bytes(name.encode())
            prefix = "../../../Example/Content/"
            rows = [{"mount": prefix + name, **value} for name, value in demo.inventory(root).items()]
            self.assertEqual(demo.verify_extracted(rows, root, prefix), 3)
            (root / "mesh.ubulk").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                demo.verify_extracted(rows, root, prefix)
            (root / "mesh.ubulk").write_bytes(b"mesh.ubulk")
            (root / "unlisted.uexp").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                demo.verify_extracted(rows, root, prefix)
            with self.assertRaisesRegex(ValueError, "Unsafe relative"):
                demo.verify_extracted([{**rows[0], "mount": prefix + "../escape"}], root, prefix)

    def test_manager_changes_only_selected_mod_rows_and_active_loadout(self):
        old = {"name": "Old", "enabled": True, "paks": {"old-pak": True}, "retain": 7}
        other = {"name": "Other", "enabled": True, "paks": {"other-pak": True}}
        before = {"Configs": {"Game": {"CurrentLoadout": "A", "ModList": [old, other],
                                      "Loadouts": {"A": [old, other], "B": [old, other]}},
                              "Other Game": {"setting": "keep"}}, "window": [4, 5]}
        unchanged = copy.deepcopy(before)
        after = demo.manager_after(before, "Game", "A", "Old", "New", "new-library-pak")
        self.assertEqual(before, unchanged)
        game = after["Configs"]["Game"]
        self.assertEqual(game["Loadouts"]["B"], [{**old, "enabled": False}, other])
        self.assertEqual(game["Loadouts"]["A"][0]["paks"], {"new-library-pak": True})
        self.assertEqual(after["Configs"]["Other Game"], before["Configs"]["Other Game"])
        self.assertEqual(after["window"], [4, 5])
        with self.assertRaisesRegex(ValueError, "Active loadout"):
            demo.manager_after(before, "Game", "B", "Old", "New", "new-library-pak")
        with self.assertRaisesRegex(ValueError, "already registered"):
            demo.manager_after(after, "Game", "A", "Old", "New", "new-library-pak")

    def test_sandbox_install_and_backup_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "new-sandbox"
            result = demo.demo(root)
            self.assertFalse(result["runtime_tested"])
            self.assertFalse(result["real_install_performed"])
            self.assertEqual(result["unrelated_mod_files_verified"], 1)
            self.assertTrue((root / "backups/transaction/Example_R1/Example_R1_P.pak").is_file())
            config = root / "example-input.json"
            spec = json.loads(config.read_text())
            spec["backup_root"] = "game/RED/Content/Paks/disabled-old"
            demo.write_json(config, spec)
            with self.assertRaisesRegex(ValueError, "entire Paks"):
                demo.make_plan(config)
            with self.assertRaisesRegex(ValueError, "must not already exist"):
                demo.demo(root)

    def test_case_duplicate_mount_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            prefix = "../../../Example/Content/"
            row = {"mount": prefix + "A.uasset", "size": 0, "sha256": "unused"}
            with self.assertRaisesRegex(ValueError, "Duplicate mount"):
                demo.verify_extracted([row, {**row, "mount": prefix + "a.uasset"}], temporary, prefix)


if __name__ == "__main__":
    unittest.main()
