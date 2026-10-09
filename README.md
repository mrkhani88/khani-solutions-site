# Khani Solutions Engineering Portfolio

Overview is served directly at https://khanisolutions.com/. The legacy https://khanisolutions.com/AISolutions/ address also displays Overview.

Five static pages: Overview, CFD simulations, Publications, Experience & projects, and Contact. All use ordinary scrolling and direct page links. The existing standalone Thermal App remains at its existing URL.

## Content and assets

- `scripts/build_portfolio.py` generates the five HTML pages from the curated content. Run `python3 scripts/build_portfolio.py` after content updates.
- `AISolutions/portfolio.css` and `portfolio.js` provide the responsive design, mobile menu, CFD category filter, publication search, and email preparation.
- The supplied October 2026 résumé is the source for professional experience and project summaries. Employer details are descriptive summaries; proprietary engineering files and figures are not published.
- Six CFD entries link to identified public posts by the LinkedIn profile `mohammadreza-khani-phd`. Players use LinkedIn's hosted embed and retain direct post links. No temporary video CDN addresses are used. Playback availability remains controlled by LinkedIn.
- Fourteen selected journal papers and two patent application records were checked against the supplied résumé, publisher records, and Google Scholar profile `ipaKdZ4AAAAJ` on October 8, 2026. Duplicate Scholar records and unrelated entries were excluded. Full-text links are included where verified. The journal issue year is used for the Neurapheresis dynamics paper (2020; originally online in 2019).
- The contact form prepares a `mailto:` draft. Visitors send it through their email app; the site does not submit or store inquiries.
- Legacy `#contact` and `#portfolio` links route to the corresponding new pages.

## Preview and deployment

Run `python3 -m http.server 4175 --bind 127.0.0.1`, then open http://127.0.0.1:4175/AISolutions/.

Pushes to `main` deploy through `.github/workflows/pages.yml`. The workflow packages `AISolutions`, the existing public assets, and the root Overview page. No private source or user files are included.

Verify desktop/phone layouts, menu keyboard behavior, filters, search and empty state, direct route refresh, internal assets/links, the embedded video, and the published revision. Do not send test inquiries.

## Logo introduction

The root Overview and legacy Overview route include the approved five-second logo handwriting intro. Persian kh is cut between its two connection bends, followed by its dot, alef connection, noon, and ye. English KHANI is written before SOLUTIONS. From 4.30 to 5.00 seconds the completed logo moves into the measured header position while the page appears. Other portfolio pages open directly.

`AISolutions/logo-intro.css`, `logo-intro.js`, and `scripts/templates/logo-intro.html` preserve the approved animation. `assets/khani-solutions-logo.png` is the exact raster artwork extracted from the existing logo SVG; the header and intro share this image. The template is hidden until JavaScript starts, so the page works without JavaScript. Skip, Escape, and reduced motion bypass the animation. Destination geometry updates on resize. Local preview controls and frozen review frames are excluded from production.

The intro plays once per browser-tab session. The shared portfolio script records the visit on every page, so returning to Overview, following page links, or refreshing does not replay it. A new tab session can show the intro again. If storage is unavailable, same-origin navigation is used as a fallback.

## Ocean design direction

The selected second design uses a light ice-blue navigation bar, a blue/teal Overview hero, and lighter content surfaces. CFD has a dark flow header; Publications has warm ivory and copper accents; Experience uses pale blue; Contact uses sage. Local Inter font files and Phosphor SVG icons include their upstream license files in `assets/`.

`ocean-flow-hero.webp` is decorative Image Generation artwork, not a CFD result. `reza-khani-portrait-cutout.webp` is an Image Generation background-removal variant of the supplied founder photo, with modest sharpening/contrast differences; original photos remain available and unchanged. Both generated assets came from the chosen mockup's art direction. Page content and professional claims remain from the existing portfolio.


### Fluid Overview layout (2026-10-09)

Overview uses viewport-based outer gutters for the hero, company row, work panels, approach and header/footer. Paragraph widths remain readable. The wider portrait (`assets/reza-khani-portrait-full-shoulders.webp`) preserves both shoulder outlines and transparent side margins; its suit edges were extended using Image Generation. The original photo and previous cutout remain intact. Rendering uses `object-fit: contain`; no horizontal crop is applied. Company marks retain their original aspect ratios; asset provenance is in `assets/company-logos/SOURCES.md`.


### Original portrait restoration (2026-10-09)

The hero now serves `reza-khani-founder-original.jpg` directly and unchanged after the generated portrait altered skin/face detail. The photo frame retains the complete source width; only the lower torso is outside the visible frame. The name/subtitle is a figure caption in normal document flow beneath the image, on the navy background. Generated cutouts are retained as historical assets but are no longer used by Overview.


### Warm portrait background (2026-10-09)

Overview uses `assets/portrait-warm-background.webp`, a background-only Image Generation extension based on the warm, defocused autumn setting in the original portrait. It contains no person. The original photograph is still served unchanged as a separate image; the extension cannot alter its face or skin detail. Navy text and a cream caption surface provide contrast against the golden background. The CFD page retains its existing flow artwork.

### Seamless portrait and Overview palette (2026-10-09)

CSS masks now feather the original photograph's outer edges into the hero backdrop. The original JPEG remains unchanged, with no facial retouching or image filter. The caption stays beneath the image, centered on the hero background. The entire Overview page now shares warm cream surfaces, bronze accents, navy text and a deep brown footer. The palette is scoped to `.page-index`, preserving the other portfolio pages' individual colors. Header, company row, work panels and approach section retain their fluid width.

### Portrait outline correction (2026-10-09)

The broad feathered rectangle still left a visible patch around the portrait. It is now replaced by `assets/portrait-contour-mask.svg`, a presentation mask following the original hair, ears and shoulder outline. The original JPEG remains the image source and is unchanged. Only the lower torso and the source photograph's right boundary fade into the hero. The caption remains outside the photo.

### Original scenery with blue lighting (2026-10-09)

Overview restores the original photo, including its woodland background. The contour and body fades are no longer used. The image retains its full source width, cropping only the lower torso; the caption sits in a cream band beneath the scene. Desktop rendering anchors the photo to the right edge. A background-only panoramic asset extends the woodland to the left, while `original-background-edge.svg` references unchanged original JPEG bytes to match the joining colors. This decorative edge extension is softly blurred; the portrait is not filtered. Blue lighting is a separate CSS overlay behind the left copy, with white text and gold accents. Smaller layouts stack the copy and original photo.

Generated background: `assets/woodland-extension-v2.webp` (2172×724), using the built-in Image Generation tool. Source: `/Users/reza/.codex/generated_images/01a11d13-3e38-7a43-97bc-1de87e0db2de/exec-c6506a9c-de9f-4163-83f6-4cf40babb9c5.png`. Prompt: create a panoramic 3:1 extension of the original photograph's defocused woodland backdrop, matching cream top highlights, golden ochre/taupe/olive forms and the upper photograph's left-edge colors. No person, text, border or watermark; no blue tint, since that is applied separately in CSS. The source portrait file remains unchanged.
