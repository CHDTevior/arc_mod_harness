"""Synthetic UE-style T/Q/S arithmetic; Python 3.10+, standard library only.

Run: python skills/arc-mod-harness/examples/retarget_tqs_demo.py
All samples are invented. No game assets, retarget solver, or UE API is used.
Vectors share one coordinate system; unit quaternions are XYZW. This example
covers nonnegative scales and already representable world T/Q/S, not shear.
"""

from dataclasses import dataclass
import json
from math import isclose, sqrt


@dataclass(frozen=True)
class TQS:
    t: tuple[float, float, float]
    q: tuple[float, float, float, float]
    s: tuple[float, float, float]


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def mul(a, b):
    return tuple(x * y for x, y in zip(a, b))


def qinv(q):
    return (-q[0], -q[1], -q[2], q[3])  # Unit quaternion conjugate.


def qmul(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X + x*W + y*Z - z*Y, w*Y - x*Z + y*W + z*X,
            w*Z + x*Y - y*X + z*W, w*W - x*X - y*Y - z*Z)


def rotate(q, v):
    return qmul(qmul(q, (*v, 0.0)), qinv(q))[:3]


def divide_axis(n, d, source_local):
    if d != 0.0:  # A tiny nonzero parent scale must not become 0 or 1.
        return n / d
    if not isclose(n, 0.0, abs_tol=1e-12):
        raise ValueError("Nonzero target on a collapsed parent axis has no solution")
    if source_local is None:
        raise ValueError("0/0 has no unique local value; supply known source local")
    return source_local


def to_local(parent, world, source_local=None):
    delta = rotate(qinv(parent.q), add(world.t, tuple(-x for x in parent.t)))
    fallback_t = source_local.t if source_local else (None,) * 3
    fallback_s = source_local.s if source_local else (None,) * 3
    return TQS(tuple(divide_axis(n, d, f) for n, d, f in
                     zip(delta, parent.s, fallback_t)),
               qmul(qinv(parent.q), world.q),
               tuple(divide_axis(n, d, f) for n, d, f in
                     zip(world.s, parent.s, fallback_s)))


def to_world(parent, local):
    return TQS(add(parent.t, rotate(parent.q, mul(parent.s, local.t))),
               qmul(parent.q, local.q), mul(parent.s, local.s))


def close_vector(actual, expected):
    assert len(actual) == len(expected)
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
               for a, b in zip(actual, expected)), (actual, expected)


def close_tqs(actual, expected):
    close_vector(actual.t, expected.t)
    close_vector(actual.s, expected.s)
    # q and -q encode the same rotation.
    sign = 1 if sum(mul(actual.q, expected.q)) >= 0 else -1
    close_vector(actual.q, tuple(sign * x for x in expected.q))


def main():
    h = sqrt(0.5)
    identity = (0.0, 0.0, 0.0, 1.0)
    parent = TQS((10, -2, 1), (0, 0, h, h), (2, 3, 0.5))
    world = TQS((4, 6, 4), (0.5, 0.5, 0.5, 0.5), (1, 6, 2))

    # Independent hand calculation: (4,2,6) * (2,3,.5) = (8,6,3).
    # A +90 degree Z rotation maps that to (-6,8,3); add (10,-2,1).
    # Rz(90) Rx(90) cycles basis x->y, y->z, z->x, fixing Q order.
    expected_local = TQS((4, 2, 6), (h, 0, 0, h), (0.5, 2, 4))
    close_tqs(to_local(parent, world), expected_local)
    for basis, expected in [((1, 0, 0), (0, 1, 0)),
                            ((0, 1, 0), (0, 0, 1)),
                            ((0, 0, 1), (1, 0, 0))]:
        close_vector(rotate(world.q, basis), expected)

    hidden = TQS(world.t, world.q, (1e-10, 6e-10, 2e-10))
    raw_world = [world, world, hidden, hidden, world, world]
    raw_indices = tuple(range(6))
    seconds = tuple(i / 60 for i in raw_indices)
    # Invented clip declares a final 1/60 s hold. Read real SeqLength separately;
    # frames / rate is not a universal rule for sampled animation resources.
    sequence_length, interpolation = 0.1, "Step"
    # Keep every raw sample and its original clock; no deduplication/resampling.
    output = [(i, t, to_local(parent, w))
              for i, t, w in zip(raw_indices, seconds, raw_world)]
    assert tuple(row[0] for row in output) == raw_indices
    assert tuple(row[1] for row in output) == seconds
    holds = [(i - 1, i) for i in range(1, 6) if raw_world[i] == raw_world[i - 1]]
    assert holds == [(0, 1), (2, 3), (4, 5)]
    assert all(output[a][2] == output[b][2] for a, b in holds)
    assert all(0 < s < 1e-8 for s in output[2][2].s)
    for (_, _, local), target in zip(output, raw_world):
        close_tqs(to_world(parent, local), target)

    tiny = TQS((0, 0, 0), identity, (1e-9, 2, 3))
    tiny_world = TQS((4e-9, 6, 12), identity, (5e-10, 4, 6))
    close_tqs(to_local(tiny, tiny_world), TQS((4, 3, 4), identity, (0.5, 2, 2)))

    collapsed = TQS((0, 0, 0), identity, (0, 2, 3))
    collapsed_world = TQS((0, 6, 12), identity, (0, 4, 6))
    known_local = TQS((7, 3, 4), identity, (9, 2, 2))
    recovered = to_local(collapsed, collapsed_world, known_local)
    assert recovered == known_local
    close_tqs(to_world(collapsed, recovered), collapsed_world)
    alternative = TQS((-13, 3, 4), identity, (17, 2, 2))
    close_tqs(to_world(collapsed, alternative), collapsed_world)  # Non-unique.
    invalid = [TQS((1, 6, 12), identity, (0, 4, 6)),
               TQS((0, 6, 12), identity, (1, 4, 6))]
    for target, fallback in [(collapsed_world, None)] + [(w, known_local) for w in invalid]:
        try:
            to_local(collapsed, target, fallback)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected an underdetermined or impossible solve")
    print(json.dumps({"fixture": "synthetic; mathematical checks passed",
                      "frames": len(output), "sequence_length": sequence_length,
                      "interpolation": interpolation, "preserved_holds": holds,
                      "hand_calculated_local_translation": list(expected_local.t),
                      "near_zero_scales_preserved": True,
                      "zero_scale_nonuniqueness_and_rejection_checked": True}, indent=2))


if __name__ == "__main__":
    main()
