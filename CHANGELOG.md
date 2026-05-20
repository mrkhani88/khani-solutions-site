# Website Log

## May 18, 2026

- Published the first Khani Solutions public website.
- Connected `khanisolutions.com` and `www.khanisolutions.com` through Cloudflare DNS.
- Enabled GitHub Pages and HTTPS.
- Added a public website log section.
- Updated the page to use section-by-section vertical snap scrolling.
- Improved mobile layout behavior for phone-size screens.
- Added phone and request type fields to the public contact form email workflow.
- Built a local-only admin Requests panel for managing leads and client inquiries.
- Added the Khani Solutions SVG logo to the website header and browser favicon.
- Tightened phone scrolling so swipes transition section-by-section like a vertical feed.
- Added automatic responsive panel fitting for phone and browser window sizes.
- Removed the visible Website log section from the customer-facing page.
- Updated Reza Khani's public title to Founder & CEO.
- Replaced the generated SVG mark with the provided Khani Solutions logo image.
- Simplified the public website into five main sections for a cleaner minimalist flow.
- Restored feed-style one-panel scrolling as a permanent website behavior across phone and desktop sizes.
- Updated the public website to a black, charcoal, gray, and white theme with gold and blue headline accents.
- Added a 1.5-second logo intro animation that runs on each page open or refresh.

## May 19, 2026

- Updated the mobile menu so it closes when the user taps outside it or presses Escape.
- Matched the dropdown menu to the five main panels: Home, Services, Process, Founder, and Pricing.
- Enlarged the intro logo so it starts near the shortest panel side before moving into the header.
- Stabilized MacBook trackpad scrolling so one two-finger swipe moves only one panel and ignores inertia.
- Updated the intro logo animation to use a white logo-matched backdrop, a 1.5-second hold, and a 1-second move into the header.
- Added Codex-style blue, orange, green, and red accents so each panel has its own headline, card, and detail color.
- Simplified the public site to three panels: Home, Services, and Contact.
- Reworked the Services panel into Apple-style one-word daily automation keywords: Calls, Texts, Email, Invoices, Schedule, Leads, Website, Listings, Reviews, and Reports.
- Replaced the logo with the high-resolution PNG source and made the intro transition seamless: white background, no logo frame or shadow, and the home page appears while the logo moves to the header.
- Changed the visual system to use the existing yellow accent consistently across all pages, with white body text and yellow-highlighted titles, icons, and key boxes.
- Adjusted the Contact panel so Founder & CEO appears under Reza Khani's name and the founder photo matches the contact text block height.
- Restored the details that were removed during simplification by combining outcomes, service keywords, process, pricing, founder notes, and full intake fields into the three-panel website.
- Repointed the visible site logo back to the original-photo SVG wrapper so the intro, header, and favicon use the high-resolution PNG source instead of a low-quality fallback.
- Retuned the website theme to match the logo, using the logo's deep navy for backgrounds and its gold accent for titles, borders, buttons, and highlighted boxes.
- Rounded the logo corners while keeping the intro and header logo marks square.
- Smoothed the intro logo move so its corner shape transitions into the final header logo shape instead of snapping at the end.
- Replaced the low-resolution founder contact photo with a high-resolution original image asset and updated mobile scrolling with safer notch/home-bar spacing.
- Replaced native scroll-snap with a transform-based panel pager so phone and trackpad transitions move smoothly without back-and-forth jitter.
- Corrected the Contact panel founder photo to use the exact original portrait selected by Reza Khani.
- Added a direct image cache-buster so browsers stop showing the previous founder photo after refresh.
- Added responsive focal-point cropping so the founder photo keeps Reza's face centered as the browser or phone size changes.
- Replaced the founder photo with Reza's modified 2085x3783 portrait and kept the responsive face-centered crop.
- Published the modified founder portrait with a fresh live asset cache-buster after GitHub Pages cached the first image URL too early.
- Switched the Contact panel portrait to the direct high-resolution JPEG so the live site loads the original image dimensions reliably.
- Updated the panel-feed verification to wait for the high-resolution founder portrait before measuring live image dimensions.
- Rotated the live portrait cache key again to avoid an early GitHub Pages edge-cache miss on the previous image URL.
- Aligned the Contact portrait's left edge with the request box below it on phone layouts and added a regression check for that alignment.
- Reserved a full-width portrait column on compact Contact layouts so the text cannot overlap the photo, and constrained the text to the request box's right edge.
- Rotated the Contact portrait cache key with the copy-fit layout so live edge caches request the verified full-resolution JPEG.
- Made page refreshes and direct section-hash loads start from the Home panel, then cache-busted the live script for public publishing.
- Inlined the critical intro-logo styles so the opening animation keeps the correct logo size even if the full stylesheet is still loading.
- Updated the live panel-feed check to verify the founder image by exact original dimensions and focal readiness instead of a timing-sensitive browser completion flag.
- Fixed the panel-feed verification cleanup so successful local and live checks exit cleanly after Chrome closes.
- Gave live GitHub Pages verification a longer intro-animation wait window so phone checks do not fail while edge resources are still settling.
