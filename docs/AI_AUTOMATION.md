# AI automation page

Public route: https://khanisolutions.com/AISolutions/automation.html

Audience: business owners in Lewiston, Moscow, Pullman, Spokane and nearby towns, within approximately 150 miles of Lewiston.

The page offers website/inquiry workflows, document administration, scheduling/follow-ups, internal knowledge assistance, business dashboards, and draft quotes/invoices. Examples are illustrative and include human review. No customer testimonials, savings statistics, prices, or guaranteed integrations are asserted.

## Sources

- `scripts/templates/automation.html` owns the page content.
- `AISolutions/automation.css` and `automation.js` own styling and interaction.
- `assets/automation/` contains four optimized, custom AI-generated illustrations.
- `scripts/build_portfolio.py` publishes the page, adds the AI automation navigation link to portfolio pages, adds an Overview entry, and includes the topic on Contact.

Run `python3 scripts/build_portfolio.py` before publication. The existing GitHub Pages workflow copies these assets and deploys them with the portfolio.

## Contact behavior

The form prepares a mailto draft addressed to the same public email used by the existing Contact page. The visitor reviews and sends from their email application. There is no backend submission, automatic email delivery, or server-side storage of form entries. Direct email and telephone links are available.

## Validation

Desktop 1280 px, tablet 1024 px and mobile 390 px checked in the browser. All six workflow examples, mobile menu opening/closing, inquiry-message prefilling, images, internal anchors and navigation links verified. JavaScript syntax and whitespace checks passed. Reduced-motion preferences disable animated scrolling and effects. Static content and contact links remain usable without JavaScript.

## Artwork

Created with the built-in image_gen tool. Original PNGs, briefs/provenance and screenshots are retained in the iCloud project folder `AI Automation Deliverables`, alongside this checkout. Website versions are WebP, totaling approximately 376 KB. Each image uses a warm cream/teal/gold editorial 3D still-life direction.
