# Visual system

## Monash branch override

When the target is Monash University, read the sibling [monash-xhs-design](../monash-xhs-design/SKILL.md) and select a scene-appropriate brand direction before applying these defaults. Preserve the five-page, evidence and 1242×1660 PNG contracts, while allowing the selected layout, component arrangement and image treatment to vary. The Monash branch does not require the default single-column structure, a fixed component set or a fixed lower-page fill height. Record Monash's official rules separately from the HLS footer and content adaptations; default output uses the school Logo and HLS footer Logo together unless the user explicitly requests the Monash-only `-OmitSchoolLogo` verifier override.

## Canvas and hierarchy

- 1242×1660 pixels, 3:4, white or near-white background.
- Single-column editorial/study-guide reading flow.
- Shared left/right boundaries on at least 90% of elements.
- Inner-page effective content target: 75%–85% of the canvas.
- Inner-page content must extend to at least 1,250px from the top edge (before the footer); a large blank lower half is a failed layout even when there is no DOM overflow.
- Typography floor: page title at least 56px; section title at least 30px; ordinary body text at least 25px; captions may go down to 20px only for source context. Do not shrink text to accommodate weak content structure.
- Review at phone-like scale: if any page reads as an isolated cluster in the upper two-thirds, enlarge type and restructure with an additional evidence, action or comparison block.

## Color

- Primary layout blue: `#283E7C`. It preserves the hue of the sampled HLS blue `#1F4CCB`, while HSL saturation and lightness are each reduced by 30% (`× 0.7`) for a calmer academic tone.
- Dark blue: `#1D2E5F`.
- Soft gray-blue: `#F0F2F7`.
- Ink: `#141414`; muted: `#67636A`; divider: `#D8D5DA`.
- School logo retains its original colors. Do not recolor it to the HLS system.
- The complete HLS logo and school logo remain in their original colors; the 30% reduction applies only to layout color, not embedded brand assets or photography.
- A school's brand color may appear inside its logo or campus image but must not replace the layout primary color.

## Header

- Left: complete HLS logo in its approved blue/orange/cyan colors, not text-only `HLS COURSE NOTES`.
- Right: school crest/logo immediately before the English school name; second line is semester or page topic.
- Header remains visually light and never competes with the page title.

## Watermark

- Center every page with the italic `HLS` lettermark.
- Light gray RGB `143,150,158`, rendered at 8% CSS opacity.
- Keep it behind content and large enough to read as background identity without reducing legibility.

## Restraint

- No dashboard mosaic, glassmorphism, decorative icon piles or heavy shadows.
- Maximum three rounded containers, two icons and one emphasis box per page when the structure allows.
- Screenshots are evidence strips; use text and diagrams to explain.
