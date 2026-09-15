#!/usr/bin/env python3
"""Synthetic workflow exercise. No actual game assets, renders or human approvals."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("harness",ROOT/"skills/arc-mod-harness/scripts/harness.py")
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
spec=importlib.util.spec_from_file_location("projection",ROOT/"skills/arc-mod-harness/scripts/project_points.py")
projection=importlib.util.module_from_spec(spec);spec.loader.exec_module(projection)


def run(out):
    h.run(h.make_parser().parse_args(["init",str(out),"--name","合成演练 · 不是实际 MOD"]))
    s=h.load(out)
    s["answers"]={"intent":{"value":"比较三种眼缘参考，选择 C，保留 A/B","status":"answer","source":"synthetic demo fixture"},
                  "game_build":{"value":"synthetic-demo","status":"answer","source":"fixture"},
                  "scopes":{"value":["face"],"status":"answer","source":"fixture"}}
    s["selected_variant"]="C"
    for variant,lower in [("A",60),("B",15),("C",30)]:
        path=out/"references"/(variant+".svg")
        eye=lambda x:f'<path d="M{x} 150 Q{x+65} {150+lower} {x+130} 150 L{x+130} 120 L{x} 120Z" fill="#f2f3e8" stroke="#243c48" stroke-width="3"/><circle cx="{x+65}" cy="137" r="17" fill="#38bda9"/><circle cx="{x+65}" cy="136" r="7" fill="#132832"/><path d="M{x} 119 L{x+130} 119" stroke="#142129" stroke-width="10"/>'
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="350" viewBox="0 0 720 350"><rect width="720" height="350" fill="#bdd4db"/><text x="24" y="42" font-family="sans-serif" font-size="24">{variant} / SYNTHETIC REFERENCE</text>{eye(140)}{eye(430)}<text x="24" y="300" font-family="sans-serif" font-size="15">Diagram only - not an AI image or game render</text></svg>',encoding="utf-8")
        h.register(out,s,"ref-"+variant,"references/"+path.name,"reference","reference","reference",variant,metadata={"synthetic":True,"purpose":"workflow exercise only"},note="Hand-authored diagram. Not an actual mod or generated image.")
        f=out/"candidates"/(variant+".bin");f.write_bytes(("DEMO ONLY - "+variant).encode())
        h.register(out,s,"runtime-"+variant,"candidates/"+f.name,"runtime_file","package","runtime",variant,built_from=["ref-"+variant],metadata={"package_path":"Demo/Face.bin","synthetic":True})
    d=h.review(out,s,"reference",["ref-C"],"accept","Synthetic exercise: choose C","DEMO fixture, not a real conversation",by="demo-fixture")
    original=(out/"references/C.svg").read_bytes()
    (out/"references/C.svg").write_bytes(original+b"\n<!-- changed -->")
    stale_detected=not h.decision_current(out,s,d)
    (out/"references/C.svg").write_bytes(original)
    h.save(out,s)
    page=h.review_pack(out,s,["ref-A","ref-B","ref-C"],"reviews/compare")
    points=projection.project(h.read_json(ROOT/"examples/projection-input.json"))
    (out/"evidence/projection.svg").write_text(projection.svg(points),encoding="utf-8")
    h.write_json(out/"evidence/projection.json",points)
    plan=h.release_plan(out,s)
    report={"demo_only":True,"human_decisions_are_synthetic":True,"stale_input_detected":stale_detected,"selected_runtime_ids":[f["id"] for f in plan["files"]],"preserved_AB":all((out/"references"/(v+".svg")).is_file() for v in ("A","B")),"readiness":plan["readiness"],"review_page":page["page"]}
    assert stale_detected and report["selected_runtime_ids"]==["runtime-C"] and report["preserved_AB"] and report["readiness"]["errors"]
    h.write_json(out/"release/declared-plan.json",plan)
    h.write_json(out/"DEMO_RESULT.json",report)
    return report


if __name__=="__main__":
    if hasattr(sys.stdout,"reconfigure"):sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--out",required=True)
    args=parser.parse_args()
    try: print(json.dumps(run(Path(args.out).resolve()),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as ex:print(str(ex),file=sys.stderr);raise SystemExit(2)
