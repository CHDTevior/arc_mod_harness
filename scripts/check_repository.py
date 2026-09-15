#!/usr/bin/env python3
"""Check public repository files and local Markdown links; no remote crawling."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def check():
    names=subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT).decode().split("\0")
    files=sorted({n for n in names if n and (ROOT/n).is_file()})
    errors=[];link_count=0
    for name in files:
        path=ROOT/name
        if path.suffix.lower() in {".pak",".sig",".blend",".fbx",".uasset",".uexp",".ubulk",".wav",".mp4",".zip"}:
            errors.append(f"Unintended production binary: {name}");continue
        if path.stat().st_size>1_000_000:errors.append(f"Unexpected large file: {name}")
        try:text=path.read_text(encoding="utf-8")
        except UnicodeDecodeError:errors.append(f"Non-UTF8 file: {name}");continue
        if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})",text):errors.append(f"Possible credential: {name}")
        if re.search(r"[FH]:[\\/]",text):errors.append(f"Production machine path: {name}")
        if path.suffix==".json":
            try:json.loads(text)
            except ValueError:errors.append(f"Invalid JSON: {name}")
        if path.suffix!=".md":continue
        text=re.sub(r"```.*?```","",text,flags=re.S)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)",text):
            target=target.strip("<>").split("#",1)[0]
            if not target or "://" in target or target.startswith("mailto:"):continue
            link_count+=1
            if not (path.parent/target).exists():errors.append(f"Broken local link: {name} -> {target}")
    return {"files_checked":len(files),"local_links_checked":link_count,"errors":errors,"scope":"Static file/link/obvious-secret checks, not browser rendering or a security audit"}


if __name__=="__main__":
    result=check();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(result["errors"]))
