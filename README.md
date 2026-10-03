# Khani Solutions Public Website

Public customer-facing business site at https://khanisolutions.com/AISolutions/.

The site has two sections: **Home** and **Contact**. The Portfolio section and its Thermal App/Falcon launchers have been removed. The existing standalone Thermal App source is retained independently.

## Layout and navigation

- `AISolutions/index.html`: business content, contact form, and section navigation.
- `styles.css` and `contact-layout.css`: base brand styles.
- `AISolutions/experience.css`: responsive two-section layout, active navigation, and motion.
- `script.js`: panel navigation, input gestures, focus, direct links, and email preparation.
- `index.html`: root redirect preserving query and hash.
- `.github/workflows/pages.yml`: GitHub Pages packaging and deployment on pushes to `main`.

Motion uses a short fade and vertical offset, with a brief logo introduction once per browser-tab session. Reduced-motion preferences use a standard scrolling page. Small screens can scroll within Contact to reach every form field. Hidden panels are inert to keyboard navigation.

The contact form opens the visitor's email client. It does not submit inquiries to a backend.

## Local preview

```bash
python3 -m http.server 4174 --bind 127.0.0.1
```

Open `http://127.0.0.1:4174/AISolutions/`.

## Verification

Check desktop and phone Home/Contact layouts, the menu and its Escape/outside-click dismissal, direct `#contact` links and refresh, browser Back, wheel/swipe navigation, keyboard focus, reduced motion, and Contact overflow scrolling. Do not send test email inquiries.
