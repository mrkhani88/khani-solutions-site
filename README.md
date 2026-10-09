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
