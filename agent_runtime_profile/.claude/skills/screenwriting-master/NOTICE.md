# screenwriting-master integration notice

This ArcReel skill adapts `Shanyin-ai/shanyin-screenwriting-master` for the ArcReel agent runtime.

- Upstream repository: https://github.com/Shanyin-ai/shanyin-screenwriting-master
- Upstream author credit: Designed by @山音 / Shanyin-ai
- Upstream license: MIT License, Copyright (c) 2026 Shanyin-ai
- Imported upstream reference files are kept under `references/`.
- ArcReel-specific `SKILL.narration.md` and `SKILL.drama.md` rewrite the entry workflow so it can operate on `project.json`, `drafts/episode_N/*`, and `scripts/episode_N.json` without replacing ArcReel's deterministic generation tools.

The upstream README also asks users to keep the original author credit and not resell the skill file itself as a standalone paid product. ArcReel keeps the author credit here and treats this integration as an adapted runtime workflow, not a standalone skill resale package.