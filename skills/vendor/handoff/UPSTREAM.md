# Upstream

- Repository: https://github.com/mattpocock/skills
- Revision: 49dd158d1076134a641b33efb035946536778336
- Directory: `skills/productivity/handoff/`
- License source: `LICENSE` at that revision (MIT, Copyright 2026 Matt Pocock).
- Local changes: Removed `disable-model-invocation: true` and set `allow_implicit_invocation: true` in `agents/openai.yaml` so the model can invoke the skill in response to a user command. Clarified the description to require /handoff or an explicit user command, never unsolicited execution. Added this provenance file and a copy of the upstream license.

Pinned to the same revision as the vendored grilling wrappers. No sibling skill dependencies. Model invocation is enabled; user intent remains required by the description.
