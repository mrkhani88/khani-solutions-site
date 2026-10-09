# Ocean direction design QA

Selected source: second displayed Image Generation design, `exec-11f55d2a-0447-4e7a-ae0d-3467368aca25.png` (1496×1052), normalized to 1280×900 for comparison. Implementation: local Overview at 1280×900. Combined evidence: `/Users/reza/Documents/ChatGPT/Job/ocean-design-qa/comparison-v1.png`.

## First pass

- P2 typography: headline and brand are visibly lighter than the selected target. Increase display weight to 600 and brand weight to 700.
- P2 spacing: the hero ends 36px lower than the target, shifting the lower navigation entries down. Reduce hero-copy vertical padding, and align desktop page margins to the target's 55px inset.
- P2 image scale: portrait face is smaller and lower than in the selected design. Increase cutout height to 530px and allow its lower torso to crop below the hero.
- Colors/tokens: navy/teal/gold hero and ice-blue header are established. Use a slightly richer ice tint below the hero.
- Copy/content: retain factual existing portfolio headings and employment names. Generated mockup company logos and outdated Amazon Project Kuiper branding are replaced with truthful existing company names. The decorative 'Ocean engineering' label stays the existing professional portfolio label; it is not a claim that ocean engineering is Reza's specialty.
- Image quality: generated flow artwork is decorative, not a scientific result. The cutout keeps the supplied portrait identity but slightly changes photographic sharpening/contrast; originals remain unchanged.

## Second pass

Combined evidence: `/Users/reza/Documents/ChatGPT/Job/ocean-design-qa/comparison-v2.png`. Display weight, page inset, hero height and portrait scale corrected. The layout and color system now match the selected direction; factual source copy and text company names are intentional differences.

P2 mobile contrast: the full-height decorative background put bright flow lines behind body text. Move the asset to the lower portrait area on phones, leaving a quiet navy reading area. Phone evidence before correction: `home-phone-v1.png`.

## Final pass

Final combined evidence: `/Users/reza/Documents/ChatGPT/Job/ocean-design-qa/comparison-final.png`; focused hero comparison: `hero-comparison-final.png`. Source 1496×1052 normalized to 1280×900; implementation 1280×900 CSS pixels, 1x capture. All five required surfaces were reviewed:

- Fonts/typography: locally served variable Inter, clear display hierarchy, stronger brand/headline corrected in pass two. Source-like sans serif retained throughout. Existing accurate copy and location/PhD metadata intentionally stay, so line breaks and hero-copy position differ modestly from the concept.
- Spacing/layout: light 74px navigation, 55px desktop inset, approximately 480px hero, spacious three-column navigation below. Portrait enlarged and lower torso cropped. Responsive stacking checked at 320, 390 and 768 CSS px; no horizontal overflow. Hero/controls did not overlap.
- Colors/tokens: navy, teal, ice-blue and gold match the selected direction. Light ivory/copper Publications, pale-blue Experience and sage Contact differentiate the pages. Phone text area now stays solid navy; raster flow artwork is confined to the portrait panel.
- Image quality/assets: real logo preserved. Generated decorative flow raster has no scientific-result labels. Portrait variant preserves identity and natural proportions with minor photographic contrast/sharpening differences; originals stay unchanged. Phosphor waves/file/gear icons replace similar concept icons with actual library assets.
- Copy/content: existing résumé/project/publication/video content and links retained. Existing company names used instead of mockup's invented/unverified logo variants. No extra specialty or scientific claims added.

Interaction checks: desktop Thermal filter showed one matching simulation; mobile Free surface filter showed one; searching papers for “monkey” showed three matches and clearing restored the list; mobile menu navigated to Overview, Experience and Contact. Existing intro plays on a fresh tab and skips on returning to Overview. Local static asset/route validation passed. Browser reported no application console errors on Overview. Phone input text remains 16px, menu and filters are 44px minimum. Contact form remains the existing email-draft flow; no external message was sent. Full accessibility certification and LinkedIn cross-platform availability were outside this visual change.

No remaining P0/P1/P2 design issues. Optional P3: company logos could be sourced from approved brand files in a later pass; keep actual names for now. Tablet portrait caption is hidden because its repeated identity text would cross the suit's pale area.

Implementation checklist: selected direction implemented; source content preserved; desktop/phone/tablet inspected; core controls tested; intro session behavior retained; originals/licenses preserved.

final result: passed


## 2026-10-09 wide-layout follow-up

User reference: `Screenshot 2026-10-09 at 12.56.33 PM.png`, plus the same selected second concept. The user explicitly requested viewport-wide placement and full shoulders, overriding the prior fixed content cap. Comparison: `/Users/reza/Documents/ChatGPT/Job/wide-layout-qa/comparison.png` (selected concept left, current 1280×900 prototype right).

- P2 spacing resolved: Overview wrappers, header/footer and the lower work/approach panels now use fluid 3vw gutters, bounded at 18–80px, without a desktop maximum width. At 2560px the section edges are x76.8 and x2483.2; at 1920px x57.6 and x1862.4. Paragraphs retain readable line lengths.
- P2 portrait clipping resolved: wider 1536×1024 RGBA portrait contains both rounded shoulder outlines. Alpha bounds x248–1340 leave 16.1% left and 12.8% right transparent margins. Only the chest meets the bottom edge. Both source photo and old asset remain untouched. Suit edge extension and minor sharpening are generated. CSS uses contain; the phone image follows its natural aspect ratio. Portrait enlarged at standard desktop width to better match the chosen concept.
- P2 logo omission resolved: six actual company marks replace text names. Wisk/Alcyone/Idaho official or company-supplied assets; Boeing/Amazon LEO/Blue Origin original vector mirrors with source records. Originals and proportions retained. The row uses a clean white surface because the Alcyone press logo includes white. Current Amazon LEO and actual Alcyone mark intentionally differ from the generated concept. Sources: `assets/company-logos/SOURCES.md`.
- Fonts: local Inter and established display hierarchy retained. Colors: navy/teal/gold hero, ice-blue page, original company colors preserved. Copy: existing factual portfolio content preserved.
- Responsive browser review: 1280, 1920 and 2560px desktop; 768px tablet; 390 and 320px phones. No horizontal overflow, text/controls remain clear, shoulders remain contained. Company logos all loaded. Narrow phone menu navigated to Experience and back to Overview; the intro was hidden with `data-skipped=already-open` on return.

No remaining P0/P1/P2 issues in the requested layout scope. Images and page screenshot evidence saved under `/Users/reza/Documents/ChatGPT/Job/wide-layout-qa/`.

final result: passed


## 2026-10-09 original-photo correction

User reported that the generated portrait looked bad and the caption sat awkwardly over the suit. The earlier image-quality review missed the facial/skin differences that mattered to the user. Both generated cutouts are now removed from the Overview rendering.

The hero serves the unchanged, original 2085×3783 photograph. The frame retains the entire source width, with only a vertical lower-torso crop. No face retouching, synthetic shoulder extension, filter, sharpening or image recompression is applied. The source asset is unchanged in Git. The figure caption is in normal flow, below the photo on a solid navy background; the original background is retained to preserve the photograph exactly.

Browser checks at 1280px desktop, 768px tablet, 390px phone and 320px phone: no horizontal overflow; original image loaded; caption top equals photo-frame bottom and does not overlap it; caption remains visible at the tablet breakpoint. Evidence: `/Users/reza/Documents/ChatGPT/Job/original-portrait-qa/desktop.png` and `phone-caption.png`. Wide-screen outer gutters, company logos and navigation are preserved.

final result: passed
