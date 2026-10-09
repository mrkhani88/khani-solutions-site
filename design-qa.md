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
