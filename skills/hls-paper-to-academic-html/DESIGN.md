# HLS Academic Signal

## Brand

The system translates the HLS Logo's cobalt, orange, sky blue, forward lean, and cut corners into an academic editorial system. It must look like HLS, not a generic blue-red thesis presentation.

## Colors

```css
--hls-cobalt: #1F4CCA;
--hls-orange: #DF6941;
--hls-sky: #62BCE8;
--hls-ink: #102B5C;
--hls-blue-soft: #EAF1FF;
--hls-orange-soft: #FFF0EA;
--hls-paper: #FAFBFD;
--hls-white: #FFFFFF;
--hls-text: #1D2939;
--hls-muted: #667085;
--hls-line: #D9E2F2;
```

## Layout

- Canvas: 1080×1440.
- Use warm paper white `#FAF8F3` and a vertical editorial reading flow.
- Use cobalt for structure and orange only for risk, action, or decisive contrast.
- Preserve large empty areas; one page owns one cognitive task.
- Use cut corners, slanted rails, evidence tags, and restrained speed lines.
- Do not use full-width dark-blue title bars on every page.

## Typography

```css
font-family: Inter, Arial, "PingFang SC", "Microsoft YaHei",
  "Noto Sans CJK SC", sans-serif;
```

Chinese body text must be at least 24px in 1080×1440 screenshots. No bundled font files or online fonts.

## Logo

- Preserve aspect ratio and color.
- Content slides: approximately 5–8% of canvas width.
- Cover: no more than 12%.
- Do not crop, stretch, shadow, recolor, or redraw.

## Page Anatomy

Each standard page contains a 128px brand-blue chapter banner, title and reading purpose, a paper-source card, reading notes, unboxed vertical annotations, a dark-blue “一句话记住” bar, and an Evidence Footer. Decorative graphics cannot replace evidence.

## Guided Reading Components

- `agenda-reading`: an optional directory for decks longer than five pages; five-page decks omit it.
- `source-reading`: a compact title band above a two-column body. The left column preserves the PDF excerpt; the right column provides faithful Chinese translation, emphasis, and short reading notes.
- `figure-reading`: the paper's original figure or table occupies the main visual area; adjacent notes explain how to read it without redrawing or simplifying away uncertainty.

For guided pages, the title follows the chapter banner. Do not repeat the title inside the source or translation panel. PDF excerpts must remain legible, use `object-fit: contain`, and show the source page on the paper-card tag.

The chapter banner always uses `#1F4CCB`; chapter identity comes from the Chinese name, English name, SECTION number, and page number. Do not assign different colors to sections. Cyan is reserved for small graphic marks, never body text.

Section names must follow the actual paper structure and the page's cognitive task. Do not label pages `研究一 / 研究二` merely because they occupy slide 3 and slide 4; a single-study paper may instead use `研究模型 / 核心结果`.

Paper-card metadata must come from the current paper's authors, journal, and year. Example-paper metadata must never remain as a fallback in a rendered case when current metadata is available.
