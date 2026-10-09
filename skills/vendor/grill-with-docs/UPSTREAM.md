# Upstream

- Repository: https://github.com/mattpocock/skills
- Revision: 49dd158d1076134a641b33efb035946536778336
- Directory: `skills/engineering/grill-with-docs/`
- License source: `LICENSE` at that revision (MIT, Copyright 2026 Matt Pocock).
- Local changes: Removed `disable-model-invocation: true` from `SKILL.md` and set `allow_implicit_invocation: true` in `agents/openai.yaml`. Added a consent boundary: start the interview with documentation only on user request or acceptance of an offer (including from `/prep`); otherwise explain the possible glossary/ADR writes and ask first. Added this provenance file and a copy of the upstream license.

Requires the sibling vendored `grilling` and `domain-modeling` skills to be installed too.
