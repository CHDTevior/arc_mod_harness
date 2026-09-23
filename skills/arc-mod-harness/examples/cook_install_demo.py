#!/usr/bin/env python3
"""Read-only installation planner and isolated synthetic installation exercise.

Python 3.10+ standard library. No UE invocation, signing, or live install command.
The demo's .pak/.sig files contain labelled synthetic text, never game assets.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def contained(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


def no_links(path):
    """Reject symlinks and Windows junctions, including ancestor redirection."""
    path = Path(path).absolute()
    nodes = [path, *path.parents]
    if path.is_dir() and not path.is_symlink():
        nodes.extend(path.rglob("*"))
    for node in nodes:
        if node.exists() or node.is_symlink():
            info = node.lstat()
            require(not stat.S_ISLNK(info.st_mode)
                    and not getattr(info, "st_file_attributes", 0) & 0x400,
                    "Reparse point or symlink: " + str(node))


def relative_name(value):
    name = PurePosixPath(value)
    require(value and "\\" not in value and ":" not in value
            and not name.is_absolute() and ".." not in name.parts
            and str(name) == value and name.parts, "Unsafe relative name")
    return name


def inventory(root):
    no_links(root)
    require(Path(root).is_dir(), "Missing directory: " + str(root))
    return {p.relative_to(root).as_posix(): {"size": p.stat().st_size,
                                           "sha256": digest(p)}
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def verify_extracted(records, extracted_root, mount_prefix):
    """Use ONE observed extraction root; never guess/remove arbitrary prefixes."""
    require(mount_prefix.endswith("/"), "Mount prefix must end in slash")
    expected = {}
    folded = set()
    for row in records:
        mount = row["mount"]
        require(mount.startswith(mount_prefix), "Unexpected mount root")
        relative = str(relative_name(mount[len(mount_prefix):]))
        require(relative.casefold() not in folded, "Duplicate mount ignoring case")
        folded.add(relative.casefold())
        expected[relative] = {"size": row["size"], "sha256": row["sha256"]}
    require(expected, "Empty cooked inventory")
    actual = inventory(Path(extracted_root))
    require(actual == expected, "Extracted file set, size or SHA256 mismatch")
    return len(actual)


def manager_after(before, game, active, old_name, new_name, library_pak):
    """Historical Unverum schema. Preserve all fields except the named mod rows."""
    require(old_name != new_name, "Old and new revision must differ")
    result = copy.deepcopy(before)
    section = result["Configs"][game]
    require(section["CurrentLoadout"] == active, "Active loadout changed")
    require(active in section["Loadouts"], "Missing active loadout")
    lists = [section["ModList"], *section["Loadouts"].values()]
    require(all(isinstance(rows, list) for rows in lists), "Unknown manager schema")
    require(sum(row["name"] == old_name for row in section["ModList"]) == 1,
            "Expected exactly one old ModList entry")
    require(not any(row["name"].casefold() == new_name.casefold()
                    for rows in lists for row in rows), "New revision already registered")
    for rows in lists:
        for row in rows:
            if row["name"] == old_name:
                row["enabled"] = False
    entry = {"name": new_name, "enabled": True, "paks": {library_pak: True}}
    section["ModList"].insert(0, copy.deepcopy(entry))
    section["Loadouts"][active].insert(0, copy.deepcopy(entry))

    def unrelated(config):
        other = copy.deepcopy(config)
        target = other["Configs"][game]
        target["ModList"] = [r for r in target["ModList"]
                             if r["name"] not in (old_name, new_name)]
        for key, rows in target["Loadouts"].items():
            target["Loadouts"][key] = [r for r in rows
                                       if r["name"] not in (old_name, new_name)]
        return other

    require(unrelated(result) == unrelated(before), "Unrelated configuration changed")
    return result


def make_plan(config_path):
    """Read configured files; return a plan. Never write to configured paths."""
    config_path = Path(config_path).resolve()
    spec = json.loads(config_path.read_text(encoding="utf-8-sig"))

    def located(key):
        path = Path(spec[key])
        if not path.is_absolute():
            path = config_path.parent / path
        no_links(path)
        return path.resolve()

    paks, backup = located("paks_root"), located("backup_root")
    require(not contained(backup, paks) and not contained(paks, backup),
            "Backup and entire Paks tree must be disjoint")
    old_name, new_name = spec["old_name"], spec["new_name"]
    require(len(relative_name(old_name).parts) == 1
            and len(relative_name(new_name).parts) == 1, "Mod name must be one directory")
    live = paks / "~mods"
    old, new = live / old_name, live / new_name
    library_root, source = located("library_root"), located("release_root")
    library = library_root / new_name
    require(not new.exists() and not library.exists() and not backup.exists(),
            "New destination or transaction already exists")
    require(not contained(library_root, paks) and not contained(source, paks),
            "Library and release must be outside Paks")
    no_links(old)
    old_pak = old / str(relative_name(spec["old_pak"]))
    require(digest(old_pak) == spec["old_pak_sha256"], "Old installed PAK changed")
    actual = inventory(source)
    require(actual == spec["release_files"], "Release file inventory/hash mismatch")
    pak, sig = str(relative_name(spec["pak"])), str(relative_name(spec["sig"]))
    require(pak in actual and sig in actual and Path(pak).suffix == ".pak"
            and Path(sig).suffix == ".sig" and Path(pak).with_suffix(".sig") == Path(sig),
            "Expected matching PAK/SIG filenames")
    require(actual[sig]["sha256"] == spec["sig_provenance"]["sha256"]
            and spec["sig_provenance"]["kind"] == "copied_compatibility_sidecar",
            "Sidecar provenance/hash mismatch; no signature generated")
    manager = located("manager_config")
    before = json.loads(manager.read_text(encoding="utf-8-sig"))
    after = manager_after(before, spec["game"], spec["active_loadout"],
                          old_name, new_name, str(library / pak))
    other = {name: value for name, value in inventory(live).items()
             if name.split("/", 1)[0] != old_name}
    return {"status": "PLAN_ONLY", "installed": False, "runtime_tested": False,
            "config_before_sha256": digest(manager), "config_after": after,
            "source_files": actual, "unrelated_mod_files": other,
            "paths": {"source": str(source), "old": str(old), "new": str(new),
                      "library": str(library), "backup": str(backup),
                      "manager": str(manager)},
            "actions": ["Recheck closed processes, all hashes and path boundaries",
                        "Back up raw manager config outside the entire Paks tree",
                        "Stage release and copy to manager library; verify every file",
                        "Move only named old live mod to backup; move verified stage live",
                        "Write reviewed manager config if its before hash still matches",
                        "Verify installed files and all unrelated files/configuration",
                        "Record game validation separately against exact installed hash"]}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def demo(destination):
    """Only this function mutates an installation, entirely in a new sandbox."""
    root = Path(destination).absolute()
    no_links(root.parent)
    require(not root.exists(), "Demo destination must not already exist")
    root.mkdir(parents=True)
    root = root.resolve()
    paks = root / "game/RED/Content/Paks"
    live = paks / "~mods"
    release = root / "release/Example_R2"
    old = live / "Example_R1"
    manager = root / "manager/Config.json"
    for path in (old, live / "Unrelated", release, manager.parent / "Mods"):
        path.mkdir(parents=True)
    (old / "Example_R1_P.pak").write_text("SYNTHETIC OLD PAK; NOT UE DATA\n")
    (live / "Unrelated/keep.txt").write_text("preserve unrelated mod\n")
    (release / "Example_R2_P.pak").write_text("SYNTHETIC NEW PAK; NOT UE DATA\n")
    (release / "Example_R2_P.sig").write_text("SYNTHETIC COPIED SIDECAR; NOT A SIGNATURE\n")
    old_row = {"name": "Example_R1", "enabled": True, "paks": {"old-library-pak": True}}
    other_row = {"name": "Other", "enabled": True, "paks": {"other-library-pak": True},
                 "preserved_custom_field": [1, 2]}
    before = {"theme": "example", "Configs": {
        "Example Game": {"CurrentLoadout": "Default", "ModList": [old_row, other_row],
                         "Loadouts": {"Default": [old_row, other_row], "Alternate": [old_row]}},
        "Other Game": {"untouched": True}}}
    write_json(manager, before)
    spec = {"paks_root": "game/RED/Content/Paks", "backup_root": "backups/transaction",
            "library_root": "manager/Mods", "release_root": "release/Example_R2",
            "manager_config": "manager/Config.json", "game": "Example Game",
            "active_loadout": "Default", "old_name": "Example_R1", "new_name": "Example_R2",
            "old_pak": "Example_R1_P.pak", "old_pak_sha256": digest(old / "Example_R1_P.pak"),
            "pak": "Example_R2_P.pak", "sig": "Example_R2_P.sig", "release_files": inventory(release),
            "sig_provenance": {"kind": "copied_compatibility_sidecar", "source_id": "synthetic-prior-release",
                               "sha256": digest(release / "Example_R2_P.sig")}}
    config = root / "example-input.json"
    write_json(config, spec)
    plan = make_plan(config)
    write_json(root / "plan.json", plan)
    paths = {key: Path(value) for key, value in plan["paths"].items()}
    require(all(contained(p, root) for p in paths.values()), "Demo escaped sandbox")
    paths["backup"].mkdir(parents=True)
    shutil.copy2(manager, paths["backup"] / "Config.before.json")
    stage = paths["backup"] / "stage"
    shutil.copytree(release, stage)
    shutil.copytree(release, paths["library"])
    require(inventory(stage) == plan["source_files"]
            and inventory(paths["library"]) == plan["source_files"], "Stage mismatch")
    shutil.move(str(old), str(paths["backup"] / "Example_R1"))
    shutil.move(str(stage), str(paths["new"]))
    require(digest(manager) == plan["config_before_sha256"], "Manager changed since plan")
    write_json(manager.with_suffix(".candidate.json"), plan["config_after"])
    os.replace(manager.with_suffix(".candidate.json"), manager)
    require(inventory(paths["new"]) == plan["source_files"], "Installed mismatch")
    remaining = {k: v for k, v in inventory(live).items() if k.split("/", 1)[0] != "Example_R2"}
    require(remaining == plan["unrelated_mod_files"], "Unrelated mod changed")
    require(json.loads(manager.read_text(encoding="utf-8")) == plan["config_after"], "Config mismatch")
    result = {"status": "SYNTHETIC_SANDBOX_PASS", "files_verified": len(plan["source_files"]),
              "unrelated_mod_files_verified": len(remaining), "real_pak_tested": False,
              "real_install_performed": False, "runtime_tested": False, "one_click_tested": False}
    write_json(root / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Create a NEW isolated synthetic sandbox").add_argument("destination")
    commands.add_parser("plan", help="Read config and print plan; no installation writes").add_argument("config")
    extraction = commands.add_parser("verify-extract", help="Check ALL extracted files against manifest")
    extraction.add_argument("manifest", help="JSON with mount_prefix and files[{mount,size,sha256}]")
    extraction.add_argument("extracted_root")
    args = parser.parse_args()
    if args.command == "demo":
        result = demo(args.destination)
    elif args.command == "plan":
        result = make_plan(args.config)
    else:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        count = verify_extracted(manifest["files"], args.extracted_root, manifest["mount_prefix"])
        result = {"status": "ALL_EXTRACTED_FILES_HASH_VERIFIED", "files": count, "runtime_tested": False}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
