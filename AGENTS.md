# Working on this repository

This repository is the reusable harness, not the Happy Chaos production workspace.
Keep the installed skill self-contained under `skills/arc-mod-harness`.
Use Python 3.10+ standard library for the portable tools. Run
`python -m unittest discover -s tests -v` after behavioral changes.

Keep the case study's observations distinct from proposed improvements. An AI
reference, a DCC render, an engine preview, and a live game capture are different
evidence. Do not upgrade a recorded claim to a verified fact. Never include game
binaries, third-party meshes, voice models, private transcripts or machine paths
in this public repository. The case source ledger contains relative identifiers
and digests, not redistributed assets.

Changes to a reviewed artifact or its inputs must invalidate the old decision.
Only record a human decision after an actual user statement. Keep documented
limits, CLI help and executable behavior consistent.
