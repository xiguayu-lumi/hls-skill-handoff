---
name: xiaohongshu-overseas-observer-cover
description: "Create polished 3:4 Xiaohongshu study-abroad magazine covers in the “THE OVERSEAS OBSERVER” house style: warm paper background, bilingual editorial typography, a narrow right journal rail, and a bottom vintage European children’s-book illustration. Use for 留学封面、外刊风封面、杂志感封面、THE OVERSEAS OBSERVER 系列、留学情绪或学习主题封面. Do not use for photoreal campus ads, price-led tutoring posters, or unrelated poster styles."
---

# Xiaohongshu Overseas Observer Cover

## Mission

Create one finished 1080×1440 PNG cover plus its editable content specification. The result must feel like an original editorial series, not a pixel-for-pixel copy of any reference.

The final deliverable is the fully composed magazine cover shown by the approved reference system: masthead, bilingual editorial text, right journal rail, rules, and bottom illustration panel on one 3:4 canvas. A standalone bottom illustration is only an intermediate asset and must never be presented or described as the finished cover.

The approved visual direction is documented in:

- `assets/approved-reference-cover.png`
- `references/design-language.md`
- `references/illustration-style.md`
- `references/qa-rubric.md`

## Non-negotiable rules

1. Use a 3:4 vertical canvas, normally 1080×1440 px.
2. Render all Chinese and English typography deterministically with code. Never ask an image-generation model to render the final cover text.
3. Generate or source only the bottom illustration panel, then compose typography and rules with `scripts/render_cover.py`.
4. Keep the illustration completely below the horizontal panel boundary. The girl’s head, hair, luggage, cat, or any object must not cross into the text area.
5. Keep the warm off-white paper area uncluttered. No emojis, stickers, gradients, neon colors, glossy 3D, or excessive decorative icons.
6. Use one globe motif at most. Do not use the original atom icon from the reference series.
7. Do not include price, tutoring claims, logos, QR codes, contact details, or watermarks unless the user explicitly asks.
8. Avoid exact copying of another creator’s headline, wording, illustration, or layout measurements. Preserve the house language while creating original content.
9. Chinese text must be correct, legible, and free of garbled glyphs. English must be proofread.
10. When the user asks for a revision, change only the requested layer unless the change causes a clear layout conflict.
11. Do not stop after generating the illustration. For a cover request, completion requires composition with `scripts/render_cover.py`, visual inspection of the resulting full PNG, automated validation, and a QA note.
12. In the final response, lead with the full cover PNG. Link or show the standalone illustration only as a secondary production asset when it helps the user review that layer.

## Default output files

Create:

- `output/<slug>.png` — final 1080×1440 cover
- `output/<slug>.yaml` — exact content and layout specification
- `output/<slug>-illustration.png` — bottom illustration asset
- `output/<slug>-qa.md` — short QA report

## Required inputs

Resolve these from the user’s message and supplied references:

- topic
- Chinese main headline
- English headline
- Chinese summary
- English summary
- illustration concept

Optional:

- year, default `2026`
- issue sections, default house sections
- illustration panel color
- mood
- exact fonts or local font paths

Ask one concise clarification only when the topic or intended headline cannot be inferred. Otherwise proceed with sensible defaults.

## Content rules

### Chinese headline

- Prefer 14–22 Chinese characters.
- Use a decisive, natural observation rather than a generic slogan.
- Break into 2–3 manually authored lines.
- Each line should feel balanced; avoid a single orphan character.
- Do not use punctuation at both the end of every line and the end of the full headline.

Good pattern:

- 别急着融入
- 先找到自己
- 在异国的节奏

### English headline

- Prefer 8–16 words.
- Use sentence case or title case consistently.
- Break into 1–2 lines.
- It should complement the Chinese headline, not mechanically translate every word.

### Summary

- English: about 22–42 words, usually 2–3 short lines.
- Chinese: about 30–55 Chinese characters, usually 2 lines.
- Explain the headline; do not repeat it.
- Keep the tone reflective, practical, and calm.
- Keep the summary measure visibly narrower than the full left editorial column, normally about 78–84% of that column. Leave deliberate white space before the right Journal rule.

## House layout

Start from `templates/cover-spec.yaml`.

### Canvas and columns

- Canvas: 1080×1440.
- Left editorial column: about 80% of width.
- Right journal rail: about 18% of width.
- A thin olive-gray vertical rule separates the rail.
- Bottom illustration panel spans the full canvas width.

### Visual hierarchy

1. Masthead: `THE OVERSEAS / OBSERVER`.
2. English article headline.
3. Oversized Chinese headline.
4. English summary.
5. Chinese summary.
6. Bottom illustration.
7. Right rail metadata.

### Typography

Use locally installed fonts. Do not bundle or distribute font files.

Preferred families:

- English display: Didot, Bodoni, Libre Bodoni, Noto Serif Display Black, or another high-contrast editorial serif.
- English text: Times New Roman, EB Garamond, Noto Serif, or similar.
- Chinese main headline: Source Han Serif / Noto Serif CJK Bold or Heavy, Songti SC Bold, SimSun Bold-like alternative.
- Chinese body: Source Han Serif / Noto Serif CJK Regular, Songti SC, SimSun.

The Chinese main headline is the primary story hook. Use a genuine Bold, Heavy, or Black Song/Ming weight and a visibly larger scale than body copy; do not accept a thin regular SimSun title when a heavier CJK serif is locally available.

If no suitable Chinese font is found, stop with a clear font-path request rather than silently substituting a font without Chinese glyphs.

### Core palette

- Paper: `#F6F2E8`
- Ink: `#11110F`
- Secondary gray: `#85827A`
- Olive accent: `#7E8768`
- Default illustration blue: `#82B7C5`

Theme colors may change, but keep them muted and retro.

## Bottom illustration language

Read `references/illustration-style.md` before creating the illustration.

Use this stable formula:

> one clear study-abroad moment + one focal character or a small group + one to three supporting props + zero to three animals + one flat muted background + generous empty space

Typical concepts:

- a new student holding books beside a vintage suitcase and a black-and-white cat
- a student with an umbrella, timetable, tote bag, and coffee
- a student working on a dissertation with books and a sleeping cat
- two students at a small study table with tea and notes
- a student waiting outside a supervisor’s office with a notebook and a quietly resting cat
- a playful metaphor scene where rabbits, geese, balloons, or oversized everyday objects express the topic without adding readable text

The illustration must:

- use thin, slightly imperfect ink outlines
- use flat low-saturation color with light colored-pencil or watercolor texture
- feel like a vintage European children’s book, not modern anime
- derive an original scene from general visual attributes rather than imitating a named artist or copying a supplied composition
- remain centered in the bottom panel
- leave at least 60 px clearance above the tallest object in the source panel
- contain no text, letters, logos, flags, university crests, watermarks, or UI elements unless explicitly required
- avoid photorealism and complex architectural scenes
- vary the cast, pose, clothing, animals, and prop logic across a series; do not default every topic to the same girl, suitcase, and cat

## Production workflow

### 1. Inspect references

Open the user’s reference images. Extract only the transferable system: hierarchy, column proportions, type scale, spacing, illustration mood, and palette. Do not copy exact editorial text or proprietary marks.

### 2. Draft the content spec

Copy `templates/cover-spec.yaml` to `output/<slug>.yaml` and fill every field.

Manually choose headline line breaks. Do not rely on automatic Chinese wrapping for the main title.

### 3. Create the illustration asset

Use the available image-generation capability to create only the bottom panel.

Prompt from `templates/illustration-prompt.md`. Require a 1080×520 or wider image with all subjects fully inside the frame and extra blank space along the top edge. Treat supplied artwork as mood and medium references only; never ask for an exact artist imitation.

If image generation is unavailable, write the final prompt to `output/<slug>-illustration-prompt.txt` and use a user-supplied illustration. Do not fake that the image was generated.

This step produces an intermediate asset, not the requested cover. Continue through composition and QA before returning a final result.

### 4. Compose the cover

Run:

```bash
python scripts/render_cover.py \
  --spec output/<slug>.yaml \
  --illustration output/<slug>-illustration.png \
  --output output/<slug>.png
```

Optional local font overrides:

```bash
python scripts/render_cover.py \
  --spec output/<slug>.yaml \
  --illustration output/<slug>-illustration.png \
  --output output/<slug>.png \
  --font-cn-title "/path/to/NotoSerifCJK-Bold.ttc" \
  --font-cn-body "/path/to/NotoSerifCJK-Regular.ttc" \
  --font-en-display "/path/to/Didot.ttf" \
  --font-en-body "/path/to/EBGaramond-Regular.ttf"
```

### 5. Inspect the rendered PNG

Open the final PNG and check it visually. Do not judge only from code or dimensions.

Run:

```bash
python scripts/validate_spec.py --spec output/<slug>.yaml
python scripts/validate_output.py \
  --spec output/<slug>.yaml \
  --illustration output/<slug>-illustration.png \
  --cover output/<slug>.png
```

Then complete the checklist in `references/qa-rubric.md` and save a short result to `output/<slug>-qa.md`.

### 6. Revise surgically

Examples:

- “文字排版换一下”：change line breaks, type scale, spacing, or summary arrangement; keep the illustration unless necessary.
- “底部人物头不要出线”：increase illustration top clearance, scale the figure down, or lower the illustration group. Never move the divider upward to hide the problem.
- “不要跟参考太像”：change masthead proportions, English headline placement, rule lengths, and rail spacing while preserving the overall editorial language.
- “AI感太强”：simplify objects, reduce texture, flatten lighting, remove overly perfect anatomy, and use more restrained hand-drawn linework.

## Definition of done

A cover is complete only when all of the following pass:

- the primary deliverable is one fully composed magazine cover, not a standalone illustration
- masthead, bilingual headlines and summaries, right journal rail, rules, and bottom illustration are all present
- 1080×1440 or exact requested 3:4 size
- all text is crisp and correct
- Chinese main title reads naturally in 2–3 balanced lines
- no text overlaps the right rail or illustration
- bottom panel begins on a clean horizontal boundary
- no part of the illustration crosses that boundary
- right rail is visually subordinate but legible
- no accidental logo, watermark, random letters, malformed hands, or nonsensical objects
- the result is recognizably part of the Overseas Observer series but not a direct copy
- final PNG, YAML spec, illustration asset, and QA note are all present
