# Xiaohongshu Overseas Observer Cover Skill

See `SKILL.md` for the Codex workflow and `../交接文档.md` for the Chinese handoff guide.

The primary deliverable is the fully composed 3:4 magazine cover. The standalone illustration is an intermediate asset and does not complete a cover request.

Quick test:

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
python scripts/validate_spec.py --spec examples/example-study-abroad.yaml
python scripts/render_cover.py \
  --spec examples/example-study-abroad.yaml \
  --illustration assets/example-illustration-panel.png \
  --output output/example-render.png
python scripts/validate_output.py \
  --spec examples/example-study-abroad.yaml \
  --illustration assets/example-illustration-panel.png \
  --cover output/example-render.png
```

The example illustration is a layout fixture, not a clean production illustration: it contains readable prop labels that would fail the manual illustration QA rule. New production illustrations must contain no letters or numbers.
