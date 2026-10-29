# Output and QA

## Automated checks

For the University of Birmingham branch, invoke `verify-carousel.ps1 -VisualProfile Birmingham` in addition to the normal arguments. Use `class="hls-footer-logo"` for each HLS footer image. This profile checks the black/white/gold tokens (inline or in directly linked local CSS) and footer signatures instead of blue, centered watermarks and HLS header placement. Five school logos, content, 1242×1660 size and five-page requirements still apply. Inspect actual rendered colors and font use visually; token presence is not a visual compliance guarantee. The fixed 1,250px fill target below is not required for this branch; use the Birmingham spacing guidance and retain meaningful readable content.

For the Monash University branch, invoke `verify-carousel.ps1 -VisualProfile Monash`. Use `class="hls-footer-logo"` for each HLS footer image and include `#006DAE` in inline CSS or a directly linked local stylesheet. By default, five school logos, five HLS footer logos, content, 1242×1660 size and five-page requirements still apply. If the user explicitly requests no school Logo, add `-OmitSchoolLogo` to the Monash command; the verifier then requires zero school-logo elements. This switch is Monash-only and must not be used to bypass another profile's school-logo contract. The Monash branch does not require the fixed 1,250px fill target or a fixed layout; inspect the selected scene direction and meaningful content visually. Monash College is excluded.

- Exactly `01.png`–`05.png`.
- Every image decodes and is exactly 1242×1660.
- Layout report contains five pages and zero overflow pages.
- In the Default profile, inner-page main content reaches at least 1,250px from the top of the canvas, excluding the footer; otherwise report excessive bottom whitespace. Birmingham and Monash use their branch-specific spacing guidance.
- In the Default profile, HTML contains five centered watermarks, five HLS header logos and five school header logos; Birmingham and Monash use their branch-specific signatures.
- Cover contains the supplied school display name.
- Inner-page chapter titles contain no question marks and no colon-separated subtitle.
- CSS contains `#283e7c`; previous bright blue `#1f4ccb` and legacy UQ purple `#51247a` are absent from layout CSS.
- No `[替换]`, `TODO`, placeholder URLs or previous-course codes remain.
- No forbidden commercial claims: 保分、包过、代写、代考、押题承诺.

## Manual checks

- Read the five images in sequence at phone-like scale.
- Confirm inner-page type meets the typography floor and the lower third contains useful information rather than blank canvas.
- Verify every inner-page chapter title is a concise noun phrase and that the cover school name is immediately discoverable.
- Compare every number and policy sentence against a screenshot or official page.
- Confirm the HLS logo is not cropped and any included school logo is not recolored or stretched; for a Monash `-OmitSchoolLogo` run, confirm the school logo is absent as requested.
- Check screenshot text remains readable and retains source context.
- Confirm the final page gives useful action without aggressive sales copy.

## Status language

- Before user review: `待审核`.
- After factual and visual approval: `已审核，待发布`.
- Only after explicit publication authorization: `已发布`.
