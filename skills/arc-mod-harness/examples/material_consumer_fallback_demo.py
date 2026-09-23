"""Synthetic section-remap/morph-usage example; no engine or game assets.

Run: python material_consumer_fallback_demo.py
This models the observed routing error, not GPU rendering or an engine adapter.
"""
from dataclasses import dataclass, replace
import json


@dataclass(frozen=True)
class Material:
    name: str
    supports_morph: bool
    depth_offset: float


@dataclass(frozen=True)
class Section:
    name: str
    raw_material_index: int
    draw_material_index: int
    has_morphs: bool


SECTIONS = (
    Section("skin_a", 0, 0, True),
    Section("hair", 1, 2, False),
    Section("skin_b", 2, 0, True),
    Section("mouth", 3, 1, True),
    Section("rigid_frame", 4, 3, False),
    Section("lens", 5, 4, False),
)
DEFAULT = Material("default_surface", False, 0.0)


def component_materials(depth_offset):
    return {
        0: Material("skin_mid", True, depth_offset),
        1: Material("mouth_mid", True, depth_offset),
        2: Material("hair_mid", True, depth_offset),
        3: Material("frame_mid", False, depth_offset),
        4: Material("lens_mid", False, depth_offset),
    }


def make_proxy(component):
    # Drawing applies the remap. The legacy usage scan uses the raw index.
    checked = {component[s.raw_material_index] for s in SECTIONS if s.has_morphs}
    rejected = {m for m in checked if not m.supports_morph}
    return {
        s.name: DEFAULT if component[s.draw_material_index] in rejected
        else component[s.draw_material_index]
        for s in SECTIONS
    }


def main():
    output = []
    for depth in (0.0, -3.0):
        component = component_materials(depth)
        before = make_proxy(component)
        assert before["rigid_frame"] is DEFAULT
        assert component[3].depth_offset == depth
        assert before["lens"] is component[4]
        # Offline asset capability fix; no runtime parameter copier.
        component[3] = replace(component[3], supports_morph=True)
        after = make_proxy(component)
        assert after["rigid_frame"] is component[3]
        assert after["rigid_frame"].depth_offset == depth
        output.append({
            "native_depth": depth,
            "before_component": "frame_mid",
            "before_actual_consumer": before["rigid_frame"].name,
            "after_actual_consumer": after["rigid_frame"].name,
            "fixed_by": "offline supports_morph flag only",
        })
    print(json.dumps({"synthetic_only": True, "checks": "PASS", "cases": output}, indent=2))


if __name__ == "__main__":
    main()
