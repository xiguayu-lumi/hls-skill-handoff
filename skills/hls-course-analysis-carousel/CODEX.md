# HLS Course Analysis Carousel Skill Rules

## Purpose

- Turn one official university course website into a five-page, evidence-backed Xiaohongshu course-analysis carousel delivered as PNG images.
- Keep research facts, interpretation, design assets, render scripts and final deliverables separated.

## Structure

- `SKILL.md`: trigger and end-to-end operating procedure.
- `references/`: detailed content, research, visual and output contracts.
- `assets/brand/`: approved reusable HLS brand assets only.
- `assets/template/`: editable five-page HTML starting point; school-specific logos and campus imagery are never bundled here.
- `scripts/`: deterministic scaffold, PNG render and image-validation helpers. `build-pdf.py` is a dormant historical helper and is not copied, required or invoked unless the user explicitly requests PDF.
- `evals/`: realistic prompts and objective acceptance criteria.

## Change discipline

- For University of Birmingham visual production, use the sibling `birmingham-xhs-design` Skill for palette, typography, Lines of intent and HLS footer signature. This school-specific branch replaces the standard blue styling only; preserve five-page evidence, size and PNG delivery contracts. Do not apply it to Birmingham City University.
- For Monash University visual production, use the sibling `monash-xhs-design` Skill for official brand rules, scene-based visual selection and relevant imagery. This branch replaces the fixed standard blue layout guidance with the selected Monash-compatible direction while preserving five-page evidence, size and PNG delivery contracts. The default course output carries five school-logo placements and five HLS footer-logo placements; `-OmitSchoolLogo` is an explicit Monash-only verifier override for user-requested school-logo omission and must not be used with another profile.

- Preserve the five-page output contract unless the user explicitly requests a different page count; every normal delivery includes only `01.png`–`05.png` as publishable artifacts.
- Use short noun-phrase chapter titles. Inner-page titles must not be questions or explanatory sentences; avoid `？`, `?`, and title-plus-subtitle constructions such as `标题：补充说明`.
- Update this file before changing the directory structure or mandatory visual rules.
- Never publish automatically. First runs are drafts pending human review and school-logo rights confirmation.
