#!/usr/bin/env python3
"""Portable mod workflow records. No external tool execution, deletion or upload."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
from datetime import datetime, timezone
from urllib.parse import quote

SKILL = Path(__file__).resolve().parents[1]
SCOPES = {"body", "outfit", "face", "animation", "material", "palette", "voice"}
STAGES = ["brief", "reference", "base", "wardrobe", "rig", "look", "voice", "motion", "package", "runtime", "delivery"]
KINDS = {"brief", "concept", "reference", "source", "dcc_capture", "projection", "engine_capture",
         "game_capture", "friend_capture", "audio", "technical_report", "package_report", "runtime_file", "stock_dependency"}
ROLES = {"source", "reference", "evidence", "runtime", "stock", "archive", "temporary"}
VISUAL = {"dcc_capture", "engine_capture", "game_capture", "friend_capture"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")


class HarnessError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise HarnessError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_path(value):
    need(isinstance(value, str) and value and "\\" not in value and ":" not in value, "Use a relative path with forward slashes")
    p = PurePosixPath(value)
    need(not p.is_absolute() and all(x not in {"", ".", ".."} for x in value.split("/")), "Path must stay inside project")
    need(not any(ord(c) < 32 for c in value), "Control characters are not allowed in paths")
    return p


def local_path(root, value):
    relative_path(value)
    base = Path(root).resolve()
    path = base / value
    cur = base
    for part in PurePosixPath(value).parts:
        cur = cur / part
        need(not cur.is_symlink() and not (hasattr(cur, "is_junction") and cur.is_junction()), "Symlink/junction paths are not supported")
        if cur.exists():
            # Python <3.12 on Windows: reject all reparse points, including junctions.
            need(not (getattr(cur.lstat(), "st_file_attributes", 0) & 0x400), "Reparse point is not supported")
    need(path.resolve().is_relative_to(base), "Resolved path escapes project")
    return path


def write_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    # Writes are serial; never use this CLI concurrently on the same project.
    need(not temp.is_symlink(), "Refusing symlink temporary state file")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load(root):
    s = read_json(local_path(root, "project.json"))
    need(isinstance(s, dict) and s.get("schema_version") == 1, "Unsupported project schema")
    for key, typ in [("answers", dict), ("artifacts", dict), ("decisions", list), ("feedback", list)]:
        need(isinstance(s.get(key), typ), f"Invalid project field: {key}")
    need(isinstance(s.get("selected_variant"), str), "Invalid selected_variant")
    for ident, a in s["artifacts"].items():
        need(ID.fullmatch(ident) and isinstance(a, dict), "Invalid artifact ID/record")
        need(a.get("kind") in KINDS and a.get("role") in ROLES and a.get("stage") in STAGES, f"Invalid artifact classification: {ident}")
        need(isinstance(a.get("metadata"), dict), f"Invalid metadata: {ident}")
        need(re.fullmatch(r"[0-9a-f]{64}", a.get("sha256", "")) is not None, f"Invalid hash: {ident}")
        need(isinstance(a.get("variant"), str), f"Invalid variant: {ident}")
        relative_path(a.get("path"))
        for field in ("dependencies", "built_from"):
            need(isinstance(a.get(field), list) and all(isinstance(v, str) for v in a[field]), f"Invalid {field}: {ident}")
    scopes(s)
    return s


def save(root, s):
    write_json(local_path(root, "project.json"), s)


def answer_value(s, key, default=None):
    return s["answers"].get(key, {}).get("value", default)


def scopes(s):
    value = answer_value(s, "scopes", [])
    need(isinstance(value, list) and all(v in SCOPES for v in value), "scopes must be a list from the supported scope names")
    return set(value)


def route(s):
    sc = scopes(s)
    active = {"brief", "reference", "package", "runtime", "delivery"}
    if sc & {"body", "outfit"}: active.add("base")
    if "outfit" in sc: active.add("wardrobe")
    if sc & {"body", "outfit", "face", "animation"}: active.add("rig")
    if sc & {"body", "outfit", "face", "material", "palette"}: active.add("look")
    if "voice" in sc: active.add("voice")
    if sc: active.add("motion")
    return [x for x in STAGES if x in active]


def eligible_questions(s):
    return [q for q in read_json(SKILL / "templates/questions.json")
            if not q.get("scopes") or scopes(s).intersection(q["scopes"])]


def closure(s, ids, fields=("dependencies", "built_from")):
    result, active = set(), set()
    def visit(ident):
        need(ident in s["artifacts"], f"Missing artifact/dependency: {ident}")
        need(ident not in active, f"Dependency cycle: {ident}")
        if ident in result: return
        active.add(ident)
        for field in fields:
            for dep in s["artifacts"][ident][field]: visit(dep)
        active.remove(ident)
        result.add(ident)
    for ident in ids: visit(ident)
    return result


def snapshot(root, s, ids):
    members = {}
    for ident in sorted(closure(s, ids)):
        a = s["artifacts"][ident]
        p = local_path(root, a["path"])
        need(p.is_file(), f"Missing file: {ident} / {a['path']}")
        need(file_hash(p) == a["sha256"], f"Stale file: {ident}; register a new revision, do not refresh old approval")
        members[ident] = digest(a)
    return digest({"members": members, "answers": s["answers"], "selected_variant": s["selected_variant"]})


def decision_current(root, s, d):
    try:
        return d["snapshot"] == snapshot(root, s, d["artifacts"])
    except (HarnessError, OSError, KeyError):
        return False


def stage_requirements(s, stage, ids):
    aa = [s["artifacts"][i] for i in ids]
    kinds = {a["kind"] for a in aa}
    requirements = {
        "brief": [{"brief"}], "reference": [{"concept", "reference", "audio"}],
        "base": [{"dcc_capture"}, {"technical_report"}],
        "wardrobe": [{"dcc_capture", "engine_capture"}],
        "rig": [{"dcc_capture", "engine_capture", "game_capture"}, {"technical_report"}],
        "look": [{"engine_capture", "game_capture"}, {"technical_report"}],
        "voice": [{"audio", "game_capture"}, {"technical_report"}],
        "motion": [{"engine_capture", "game_capture"}],
        "package": [{"package_report"}], "runtime": [{"game_capture"}],
        "delivery": [{"package_report"}]
    }
    for acceptable in requirements[stage]:
        need(kinds & acceptable, f"{stage} requires evidence kind from {sorted(acceptable)}")
    if stage == "brief":
        need(scopes(s), "Choose scopes before accepting the brief")
        need(not any(a.get("status") == "proposal" for a in s["answers"].values()), "Resolve labeled proposals into actual answers before accepting the brief")
    if stage == "base":
        views = {view for a in aa if a["kind"] == "dcc_capture" for view in a["metadata"].get("views", [])}
        need({"front", "side", "back"} <= views, "Base review needs front/side/back views")
    if stage == "motion":
        if "face" in scopes(s): need("projection" in kinds, "Face motion review needs projection evidence")
        captures = [a for a in aa if a["kind"] in {"engine_capture", "game_capture"}]
        need(any(a["metadata"].get("source_camera") and a["metadata"].get("reviewed_frames") for a in captures), "Motion review needs a source camera and explicit reviewed_frames")
    if stage == "package":
        roots = {i for i, a in s["artifacts"].items() if a["role"] == "runtime" and a["variant"] in {"shared", s["selected_variant"]}}
        need(roots, "Package review needs selected runtime files")
        linked = set().union(*(closure(s, a["built_from"]) for a in aa if a["kind"] == "package_report"))
        need(roots <= linked, "Package report must be built_from all selected runtime files")
    if stage in {"runtime", "delivery"}:
        for a in aa:
            if a["kind"] in {"game_capture", "friend_capture"}:
                linked = closure(s, a["built_from"])
                need(any(s["artifacts"][i]["kind"] == "package_report" for i in linked), "Game evidence must be built_from the tested package report")
                need(a["metadata"].get("game_build") == answer_value(s, "game_build") and a["metadata"].get("game_build"), "Game evidence must name the project's game build")
    for a in aa:
        if a["kind"] in VISUAL:
            need(a["metadata"].get("camera"), "Captures need a camera name")
        if a["kind"] == "friend_capture":
            need(a["metadata"].get("environment"), "Friend evidence needs an environment description")


def register(root, s, ident, path, kind, stage, role="evidence", variant="shared", dependencies=None, built_from=None, metadata=None, note=""):
    need(ID.fullmatch(ident) is not None and ident not in s["artifacts"], "Use a new, valid artifact ID")
    need(kind in KINDS and stage in STAGES and role in ROLES, "Invalid artifact classification")
    need(ID.fullmatch(variant) is not None, "Invalid variant")
    if role == "runtime": need(kind == "runtime_file", "Runtime entries must be real runtime_file artifacts")
    if role == "stock": need(kind == "stock_dependency", "Stock entries require stock_dependency kind")
    meta = metadata or {}
    need(isinstance(meta, dict), "metadata must be an object")
    if role == "runtime": relative_path(meta.get("package_path"))
    p = local_path(root, path)
    need(p.is_file(), "Artifact must be an existing project-local file")
    deps, built = list(dependencies or []), list(built_from or [])
    closure(s, deps + built)
    s["artifacts"][ident] = {"path": path, "kind": kind, "stage": stage, "role": role, "variant": variant,
        "sha256": file_hash(p), "bytes": p.stat().st_size, "dependencies": deps, "built_from": built,
        "metadata": meta, "source_note": note, "recorded_at": now()}


def review(root, s, stage, ids, verdict, quote_text, source, by="user"):
    need(stage in route(s), "Stage is not in this project's route")
    need(verdict in {"accept", "revise", "defer"} and quote_text.strip() and source.strip() and by.strip(), "Record an actual decision, quote, source and reviewer")
    need(ids and len(ids) == len(set(ids)), "Choose distinct reviewed artifact IDs")
    snap = snapshot(root, s, ids)
    need(all(s["artifacts"][i]["stage"] == stage for i in ids), "Reviewed artifacts must belong to the named stage")
    if verdict == "accept":
        stage_requirements(s, stage, ids)
        need(not any(f["status"] == "open" and s["artifacts"][f["artifact"]]["stage"] == stage for f in s["feedback"]), "Resolve open feedback in this stage before accepting")
    d = {"id": f"decision-{len(s['decisions']) + 1}", "stage": stage, "artifacts": ids, "verdict": verdict,
         "quote": quote_text, "source": source, "by": by, "recorded_at": now(), "snapshot": snap}
    s["decisions"].append(d)
    return d


def inspect(root, s, ready_for=None):
    errors, stages = [], {}
    for ident in s["artifacts"]:
        try: snapshot(root, s, [ident])
        except (HarnessError, OSError) as ex: errors.append(str(ex))
    for stage in route(s):
        dd = [d for d in s["decisions"] if d["stage"] == stage]
        d = dd[-1] if dd else None
        status = "pending" if not d else (d["verdict"] if decision_current(root, s, d) else "stale")
        if status == "accept":
            try:
                stage_requirements(s, stage, d["artifacts"])
                need(not any(f["status"] == "open" and s["artifacts"][f["artifact"]]["stage"] == stage for f in s["feedback"]), "Open feedback")
            except HarnessError: status = "needs_revision"
        stages[stage] = status
    # A game capture of an old package cannot validate a newer accepted package.
    package_decisions = [d for d in s["decisions"] if d["stage"] == "package"]
    current_package = package_decisions[-1] if package_decisions else None
    for stage in ("runtime", "delivery"):
        if stages.get(stage) != "accept": continue
        d = [d for d in s["decisions"] if d["stage"] == stage][-1]
        if stage == "delivery" and not any(s["artifacts"][i]["kind"] == "friend_capture" for i in d["artifacts"]): continue
        package_ids = {i for i in current_package["artifacts"] if s["artifacts"][i]["kind"] == "package_report"} if current_package else set()
        captures = [s["artifacts"][i] for i in d["artifacts"] if s["artifacts"][i]["kind"] in {"game_capture", "friend_capture"}]
        if stages.get("package") != "accept" or not package_ids or not captures or any(not package_ids <= closure(s, a["built_from"]) for a in captures):
            stages[stage] = "package_mismatch"
    if ready_for:
        try: runtime_inventory(root, s)
        except (HarnessError, OSError) as ex: errors.append(str(ex))
        selected_runtime = [a for a in s["artifacts"].values() if a["role"] == "runtime" and a["variant"] in {"shared", s["selected_variant"]}]
        if any(a["metadata"].get("synthetic") for a in selected_runtime):
            errors.append("Synthetic runtime fixtures cannot qualify as real-game readiness")
        stop = "package" if ready_for == "local-test" else "runtime"
        required = route(s)[:route(s).index(stop) + 1]
        errors += [f"Review not accepted/current: {x}" for x in required if stages[x] != "accept"]
        if ready_for == "friend-verified":
            dd = [d for d in s["decisions"] if d["stage"] == "delivery"]
            d = dd[-1] if dd else None
            need_friend = not d or stages["delivery"] != "accept" or not any(s["artifacts"][i]["kind"] == "friend_capture" for i in d["artifacts"])
            if need_friend: errors.append("No current accepted friend-machine evidence")
    return {"status": "RECORDS_OK" if not errors else "NEEDS_ATTENTION", "errors": sorted(set(errors)), "stages": stages,
            "selected_variant": s["selected_variant"], "open_feedback": [f["id"] for f in s["feedback"] if f["status"] == "open"],
            "limit": "Checks records and file identity; does not execute the game or judge aesthetics."}


def runtime_inventory(root, s):
    chosen = {"shared", s["selected_variant"]}
    roots = [i for i, a in s["artifacts"].items() if a["role"] == "runtime" and a["variant"] in chosen]
    need(roots, "No selected runtime files registered")
    snapshot(root, s, roots)
    included, stock, mounts = [], [], set()
    for ident in sorted(closure(s, roots, ("dependencies",))):
        a = s["artifacts"][ident]
        if a["role"] == "stock" and a["kind"] == "stock_dependency":
            build = a["metadata"].get("game_build")
            need(build and build != "unknown" and build == answer_value(s, "game_build"), f"Stock dependency needs matching game-build evidence: {ident}")
            stock.append(ident)
            continue
        need(a["role"] == "runtime" and a["kind"] == "runtime_file", f"Unbundled non-stock runtime dependency: {ident}")
        need(a["variant"] in chosen, f"Dependency reaches unselected variant: {ident}")
        mount = str(relative_path(a["metadata"].get("package_path")))
        need(mount.casefold() not in mounts, f"Duplicate package path: {mount}")
        mounts.add(mount.casefold())
        included.append({"id": ident, "path": a["path"], "package_path": mount, "sha256": a["sha256"], "bytes": a["bytes"]})
    return {"status": "DECLARED_GRAPH_PLAN_ONLY", "selected_variant": s["selected_variant"], "files": included,
            "stock_dependencies": stock, "excluded": sorted(set(s["artifacts"]) - set(closure(s, roots, ("dependencies",)))),
            "limit": "Inventory must be obtained by a real game/package adapter. This does not inspect a PAK."}


def release_plan(root, s):
    return {**runtime_inventory(root, s), "readiness": inspect(root, s, "share")}


def clean_plan(root, s):
    protected = set()
    for i, a in s["artifacts"].items():
        if a["role"] != "temporary": protected.update(closure(s, [i]))
    for d in s["decisions"]: protected.update(closure(s, d["artifacts"]))
    for f in s["feedback"]:
        protected.update(closure(s, [f["artifact"]] + ([f["resolved_by"]] if f.get("resolved_by") else [])))
    protected_paths = {local_path(root, s["artifacts"][i]["path"]).resolve() for i in protected}
    files = []
    for ident, a in s["artifacts"].items():
        if a["role"] != "temporary" or ident in protected: continue
        p = local_path(root, a["path"])
        if p.resolve() in protected_paths: continue
        snapshot(root, s, [ident])
        files.append({"id": ident, "path": a["path"], "sha256": a["sha256"], "bytes": p.stat().st_size})
    unique = {f["path"]: f for f in files}
    return {"status": "PLAN_ONLY_NO_DELETION", "files": list(unique.values()), "logical_bytes": sum(f["bytes"] for f in unique.values()), "protected_ids": sorted(protected)}


def review_pack(root, s, ids, out):
    snapshot(root, s, ids)
    folder = local_path(root, out)
    need(not folder.exists(), "Review output must be a new directory")
    folder.mkdir(parents=True)
    media = folder / "media"
    media.mkdir()
    cards, manifest = [], []
    for ident in ids:
        a = s["artifacts"][ident]
        ext = Path(a["path"]).suffix.lower()
        target = media / (ident + ext)
        shutil.copyfile(local_path(root, a["path"]), target)
        need(file_hash(target) == a["sha256"], "Review copy changed during copy")
        url = "media/" + quote(target.name)
        esc = html.escape
        if ext in {".png", ".jpg", ".jpeg", ".webp"}:
            element = f'<img class="annotatable" data-id="{esc(ident)}" src="{url}" alt="{esc(ident)}">'
        elif ext in {".mp4", ".webm"}:
            element = f'<video controls preload="metadata" src="{url}"></video>'
        elif ext in {".mp3", ".wav", ".ogg"}:
            element = f'<audio controls preload="metadata" src="{url}"></audio>'
        elif ext == ".svg":
            # SVG remains an image, never inline untrusted SVG/HTML script.
            element = f'<img src="{url}" alt="{esc(ident)}">'
        else:
            element = f'<a href="{url}" download>下载原始文件（不执行）</a>'
        label = "AI 概念参考 · 不是实际 MOD" if a["kind"] == "concept" else a["kind"]
        meta = esc(json.dumps(a["metadata"], ensure_ascii=False, indent=2))
        cards.append(f'<article><h2>{esc(ident)}</h2><p class="tag">{label} · variant {esc(a["variant"])}</p>{element}<details><summary>来源与镜头</summary><pre>{meta}</pre><p>{esc(a["source_note"])}</p><code>{a["sha256"]}</code></details></article>')
        manifest.append({"id": ident, **a, "review_copy": "media/" + target.name})
    template = (SKILL / "templates/review.html").read_text(encoding="utf-8")
    (folder / "index.html").write_text(template.replace("{{CARDS}}", "\n".join(cards)).replace("{{TITLE}}", html.escape(s["name"])), encoding="utf-8")
    write_json(folder / "manifest.json", {"snapshot": snapshot(root, s, ids), "artifacts": manifest})
    return {"page": str(folder / "index.html"), "manifest": str(folder / "manifest.json"), "note": "Generated review page; author must inspect the actual media."}


def make_parser():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="command", required=True)
    def cmd(name, help_text):
        c = sp.add_parser(name, help=help_text); c.add_argument("project"); return c
    c = cmd("init", "Create a new project (never overwrites)"); c.add_argument("--name", required=True)
    cmd("next", "Suggest the next relevant interview question")
    c = cmd("answer", "Record a human answer or a labeled proposal"); c.add_argument("id"); c.add_argument("value"); c.add_argument("--source", default="user"); c.add_argument("--proposal", action="store_true")
    c = cmd("brief", "Write a reviewable brief from current answers"); c.add_argument("--id", required=True); c.add_argument("--out", required=True)
    c = cmd("add", "Register an existing project-local artifact"); c.add_argument("id"); c.add_argument("path"); c.add_argument("--kind", choices=sorted(KINDS), required=True); c.add_argument("--stage", choices=STAGES, required=True); c.add_argument("--role", choices=sorted(ROLES), default="evidence"); c.add_argument("--variant", default="shared"); c.add_argument("--depends-on", nargs="*", default=[]); c.add_argument("--built-from", nargs="*", default=[]); c.add_argument("--metadata", help="Project-relative JSON file"); c.add_argument("--note", default="")
    c = cmd("select", "Record the author's selected variant"); c.add_argument("variant"); c.add_argument("--quote", required=True); c.add_argument("--source", required=True)
    c = cmd("retire", "Preserve an older artifact but exclude it from runtime roots"); c.add_argument("artifact"); c.add_argument("--note", required=True)
    c = cmd("decision", "Record an actual human decision"); c.add_argument("stage", choices=STAGES); c.add_argument("verdict", choices=["accept", "revise", "defer"]); c.add_argument("--artifacts", nargs="+", required=True); c.add_argument("--quote", required=True); c.add_argument("--source", required=True); c.add_argument("--by", default="user")
    c = cmd("feedback", "Record a localized requested change"); c.add_argument("artifact"); c.add_argument("--part", required=True); c.add_argument("--desired", required=True); c.add_argument("--preserve", required=True); c.add_argument("--frame", type=int); c.add_argument("--camera"); c.add_argument("--point", nargs=2, type=float)
    c = cmd("resolve", "Link feedback to the inspected replacement"); c.add_argument("feedback_id"); c.add_argument("--artifact", required=True); c.add_argument("--note", required=True)
    c = cmd("review-pack", "Create a local media review page"); c.add_argument("--artifacts", nargs="+", required=True); c.add_argument("--out", required=True)
    c = cmd("check", "Check records and stale files"); c.add_argument("--ready-for", choices=["local-test", "share", "friend-verified"])
    cmd("release-plan", "Validate declared runtime dependency closure (no packaging)")
    cmd("clean-plan", "List unused registered temporary files (no deletion)")
    return p


def run(args):
    root = Path(args.project).resolve()
    if args.command == "init":
        need(not root.exists(), "Project must be a new directory")
        root.mkdir(parents=True)
        for d in ("references", "source", "candidates", "evidence", "reviews", "release", "temporary"): (root / d).mkdir()
        s = {"schema_version": 1, "name": args.name, "created_at": now(), "selected_variant": "main", "answers": {}, "artifacts": {}, "decisions": [], "feedback": [], "selections": []}
        save(root, s)
        for filename in ("adapter.json", "replacement-matrix.md", "NEXT.md",
                         "base-assessment.md", "component-plan.md", "subtask-handoff.md", "surface-audit.md"):
            shutil.copyfile(SKILL / "templates" / filename, root / filename)
        return {"project": str(root), "next": "Read references/interview.md; ask one consequential question."}
    s = load(root)
    if args.command == "next":
        pending = [q for q in eligible_questions(s) if q["id"] not in s["answers"]]
        return {"question": pending[0] if pending else None, "route": route(s), "hint": "Read the conversation first; do not ask again if already answered. A short draft brief can be made now."}
    if args.command == "answer":
        need(args.id in {q["id"] for q in read_json(SKILL / "templates/questions.json")}, "Unknown question ID")
        value = [v.strip() for v in args.value.split(",") if v.strip()] if args.id == "scopes" else args.value
        previous = s["answers"].get(args.id)
        s.setdefault("answer_history", []).append({"id": args.id, "previous": previous, "at": now()})
        s["answers"][args.id] = {"value": value, "source": args.source, "status": "proposal" if args.proposal else "answer"}
        scopes(s); save(root, s); return {"saved": args.id, "route": route(s)}
    if args.command == "brief":
        out = local_path(root, args.out); need(not out.exists(), "Brief output must be new")
        need(ID.fullmatch(args.id) is not None and args.id not in s["artifacts"], "Brief needs a new valid ID")
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# {s['name']} · 制作说明草案", "", "未填写项保持未定；下列内容尚需作者审查。", ""]
        for q in eligible_questions(s):
            a = s["answers"].get(q["id"])
            lines += [f"## {q['title']}", "", (f"{a['value']} ({a['status']}; {a['source']})" if a else "待讨论 / 待检查"), ""]
        out.write_text("\n".join(lines), encoding="utf-8")
        register(root, s, args.id, args.out, "brief", "brief"); save(root, s); return {"brief": str(out)}
    if args.command == "add":
        meta = read_json(local_path(root, args.metadata)) if args.metadata else {}
        register(root, s, args.id, args.path, args.kind, args.stage, args.role, args.variant, args.depends_on, args.built_from, meta, args.note)
        save(root, s); return {"registered": args.id}
    if args.command == "select":
        need(ID.fullmatch(args.variant) is not None and args.quote.strip() and args.source.strip(), "Selection requires valid variant and actual author statement")
        s["selected_variant"] = args.variant
        s.setdefault("selections", []).append({"variant": args.variant, "quote": args.quote, "source": args.source, "at": now()})
        save(root, s); return {"selected": args.variant, "note": "Prior decisions bind to their earlier variant/context; check for staleness."}
    if args.command == "retire":
        snapshot(root, s, [args.artifact])
        need(args.note.strip(), "Explain why this artifact is retired")
        a = s["artifacts"][args.artifact]
        a.setdefault("role_history", []).append({"from": a["role"], "to": "archive", "note": args.note, "at": now()})
        a["role"] = "archive"
        save(root, s); return {"retired": args.artifact, "file_preserved": True}
    if args.command == "decision":
        result = review(root, s, args.stage, args.artifacts, args.verdict, args.quote, args.source, args.by); save(root, s); return result
    if args.command == "feedback":
        snapshot(root, s, [args.artifact])
        need(args.point is None or all(0 <= v <= 1 for v in args.point), "Point must be normalized to [0,1]")
        need(args.frame is None or args.frame >= 0, "Frame must be nonnegative")
        f = {"id": f"feedback-{len(s['feedback']) + 1}", "artifact": args.artifact, "sha256": s["artifacts"][args.artifact]["sha256"], "part": args.part, "desired": args.desired, "preserve": args.preserve, "camera": args.camera, "frame": args.frame, "screen_point": args.point, "status": "open", "at": now()}
        s["feedback"].append(f); save(root, s); return f
    if args.command == "resolve":
        snapshot(root, s, [args.artifact])
        f = next((f for f in s["feedback"] if f["id"] == args.feedback_id), None)
        need(f and f["status"] == "open" and args.note.strip(), "Choose open feedback and explain the verification")
        need(args.artifact != f["artifact"], "Resolve against a new inspected candidate, not the unchanged artifact")
        need(s["artifacts"][args.artifact]["stage"] == s["artifacts"][f["artifact"]]["stage"], "Replacement must address the same stage")
        f.update(status="resolved", resolved_by=args.artifact, resolution_note=args.note, resolved_at=now())
        save(root, s); return f
    if args.command == "review-pack": return review_pack(root, s, args.artifacts, args.out)
    if args.command == "release-plan": return release_plan(root, s)
    if args.command == "clean-plan": return clean_plan(root, s)
    return inspect(root, s, args.ready_for)


def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = run(make_parser().parse_args())
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 1 if result.get("errors") else 0
    except (HarnessError, OSError, ValueError, KeyError, TypeError) as ex:
        print(json.dumps({"error": str(ex)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
