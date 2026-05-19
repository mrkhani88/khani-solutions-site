const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const form = document.querySelector("[data-contact-form]");
const internalLinks = document.querySelectorAll('a[href^="#"]');
const introLoader = document.querySelector("[data-intro-loader]");
const introLogo = document.querySelector("[data-intro-logo]");
const headerLogo = document.querySelector(".brand-mark");
const feedScrollQuery = window.matchMedia("(prefers-reduced-motion: no-preference)");
let snapSections = [];
let feedScrollLocked = false;
let touchStartX = 0;
let touchStartY = 0;
let touchStartIndex = 0;
let touchHasPanelIntent = false;
let fitTimer;
let pageInitialized = false;
let wheelGestureTimer;
let wheelGestureDelta = 0;
let wheelGestureConsumed = false;
let wheelSuppressUntil = 0;
const densityClasses = ["is-compact", "is-tight", "is-ultra"];
const wheelGestureResetMs = 280;
const wheelGestureThreshold = 80;
const wheelTransitionSuppressMs = 1250;

function setIntroTarget() {
  if (!introLoader || !headerLogo) return;
  const target = headerLogo.getBoundingClientRect();
  const targetStyle = window.getComputedStyle(headerLogo);
  introLoader.style.setProperty("--intro-logo-end-x", `${target.left}px`);
  introLoader.style.setProperty("--intro-logo-end-y", `${target.top}px`);
  introLoader.style.setProperty("--intro-logo-end-size", `${target.width}px`);
  introLoader.style.setProperty("--intro-logo-end-radius", targetStyle.borderTopLeftRadius);
}

function runIntroAnimation() {
  if (!introLoader || !introLogo || !feedScrollEnabled()) {
    document.body.classList.remove("is-intro-running", "is-intro-revealing");
    introLoader?.classList.add("is-done");
    return;
  }

  setIntroTarget();

  window.setTimeout(() => {
    introLoader.classList.add("is-done");
    document.body.classList.remove("is-intro-running", "is-intro-revealing");
  }, 3050);
}

function updateHeader() {
  header.classList.toggle("is-scrolled", window.scrollY > 16);
}

function closeNav() {
  nav.classList.remove("is-open");
  header.classList.remove("is-open");
  navToggle.setAttribute("aria-expanded", "false");
}

window.addEventListener("scroll", updateHeader, { passive: true });
window.addEventListener("resize", scheduleFitPanels, { passive: true });
updateHeader();

navToggle.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("is-open");
  header.classList.toggle("is-open", isOpen);
  navToggle.setAttribute("aria-expanded", String(isOpen));
});

nav.addEventListener("click", (event) => {
  if (event.target instanceof HTMLAnchorElement) {
    closeNav();
  }
});

document.addEventListener("click", (event) => {
  if (!nav.classList.contains("is-open")) return;
  if (event.target instanceof Element && header.contains(event.target)) return;
  closeNav();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && nav.classList.contains("is-open")) {
    closeNav();
  }
});

function scrollToSection(hash, behavior = "smooth") {
  const target = hash === "#top" ? document.querySelector(".hero") : document.querySelector(hash);
  if (!target) return;
  document.documentElement.classList.add("is-jump-scroll");
  window.scrollTo({ top: target.offsetTop, behavior });
  window.setTimeout(() => document.documentElement.classList.remove("is-jump-scroll"), behavior === "smooth" ? 650 : 120);
}

function panelOverflows(section) {
  return section.scrollHeight > section.clientHeight + 2 || section.scrollWidth > section.clientWidth + 2;
}

function refreshSnapSections() {
  snapSections = [...document.querySelectorAll(".snap-section")];
}

function fitPanels() {
  refreshSnapSections();
  snapSections.forEach((section) => {
    section.classList.remove(...densityClasses);
    for (const densityClass of densityClasses) {
      if (!panelOverflows(section)) break;
      section.classList.add(densityClass);
    }
  });
}

function scheduleFitPanels() {
  window.clearTimeout(fitTimer);
  fitTimer = window.setTimeout(fitPanels, 80);
}

function currentSnapIndex() {
  refreshSnapSections();
  if (!snapSections.length) return 0;
  const anchor = window.scrollY + window.innerHeight * 0.5;
  return snapSections.reduce((closestIndex, section, index) => {
    const closestDistance = Math.abs(snapSections[closestIndex].offsetTop - anchor);
    const distance = Math.abs(section.offsetTop - anchor);
    return distance < closestDistance ? index : closestIndex;
  }, 0);
}

function feedScrollEnabled() {
  return feedScrollQuery.matches;
}

function scrollFeed(direction, fromIndex = currentSnapIndex()) {
  if (!feedScrollEnabled() || feedScrollLocked) return;
  refreshSnapSections();
  const nextIndex = Math.max(0, Math.min(snapSections.length - 1, fromIndex + direction));
  if (nextIndex === fromIndex) return;
  const target = snapSections[nextIndex];
  if (!target) return;
  const targetTop = target.offsetTop;
  feedScrollLocked = true;
  window.scrollTo({ top: targetTop, behavior: "smooth" });
  window.setTimeout(() => {
    if (Math.abs(window.scrollY - targetTop) > 2) {
      window.scrollTo({ top: targetTop, behavior: "auto" });
    }
  }, 980);
  window.setTimeout(() => {
    feedScrollLocked = false;
  }, 1120);
}

function resetWheelGesture() {
  wheelGestureDelta = 0;
  wheelGestureConsumed = false;
}

function sectionCanScroll(event, direction) {
  const section = event.target instanceof Element ? event.target.closest(".snap-section") : null;
  if (!section || section.scrollHeight <= section.clientHeight + 2) return false;
  if (!/(auto|scroll)/.test(getComputedStyle(section).overflowY)) return false;
  const atTop = section.scrollTop <= 2;
  const atBottom = section.scrollTop + section.clientHeight >= section.scrollHeight - 2;
  return direction > 0 ? !atBottom : !atTop;
}

function isEditableTarget(target) {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest("input, textarea, select, button, [contenteditable='true']"));
}

window.addEventListener(
  "wheel",
  (event) => {
    if (!feedScrollEnabled() || Math.abs(event.deltaY) <= Math.abs(event.deltaX) || Math.abs(event.deltaY) < 3) return;
    const now = performance.now();
    const direction = event.deltaY > 0 ? 1 : -1;
    if (sectionCanScroll(event, direction)) return;
    event.preventDefault();

    window.clearTimeout(wheelGestureTimer);
    wheelGestureTimer = window.setTimeout(resetWheelGesture, wheelGestureResetMs);

    if (now < wheelSuppressUntil || wheelGestureConsumed) return;

    wheelGestureDelta += event.deltaY;
    if (Math.abs(wheelGestureDelta) < wheelGestureThreshold) return;

    wheelGestureConsumed = true;
    wheelSuppressUntil = now + wheelTransitionSuppressMs;
    scrollFeed(wheelGestureDelta > 0 ? 1 : -1);
  },
  { passive: false },
);

window.addEventListener(
  "touchstart",
  (event) => {
    if (!feedScrollEnabled() || event.touches.length !== 1 || isEditableTarget(event.target)) return;
    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
    touchStartIndex = currentSnapIndex();
    touchHasPanelIntent = false;
  },
  { passive: true },
);

window.addEventListener(
  "touchmove",
  (event) => {
    if (!feedScrollEnabled() || event.touches.length !== 1 || isEditableTarget(event.target)) return;
    const touch = event.touches[0];
    const deltaX = touch.clientX - touchStartX;
    const deltaY = touch.clientY - touchStartY;
    if (Math.abs(deltaY) <= 14 || Math.abs(deltaY) <= Math.abs(deltaX)) return;
    touchHasPanelIntent = true;
    event.preventDefault();
  },
  { passive: false },
);

window.addEventListener(
  "touchend",
  (event) => {
    if (!feedScrollEnabled() || !touchHasPanelIntent || isEditableTarget(event.target)) return;
    const touch = event.changedTouches[0];
    if (!touch) return;
    const deltaY = touch.clientY - touchStartY;
    if (Math.abs(deltaY) < 42) return;
    scrollFeed(deltaY < 0 ? 1 : -1, touchStartIndex);
    touchHasPanelIntent = false;
  },
  { passive: true },
);

window.addEventListener("touchcancel", () => {
  touchHasPanelIntent = false;
});

window.addEventListener("keydown", (event) => {
  if (!feedScrollEnabled() || isEditableTarget(event.target)) return;
  const downKeys = ["ArrowDown", "PageDown", " "];
  const upKeys = ["ArrowUp", "PageUp"];
  if (downKeys.includes(event.key) && !event.shiftKey) {
    event.preventDefault();
    scrollFeed(1);
  } else if (upKeys.includes(event.key) || (event.key === " " && event.shiftKey)) {
    event.preventDefault();
    scrollFeed(-1);
  } else if (event.key === "Home") {
    event.preventDefault();
    scrollToSection("#top");
  } else if (event.key === "End") {
    event.preventDefault();
    refreshSnapSections();
    snapSections[snapSections.length - 1]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

internalLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const hash = link.getAttribute("href");
    if (!hash || hash === "#") return;
    event.preventDefault();
    scrollToSection(hash);
    history.pushState(null, "", hash);
  });
});

window.addEventListener("hashchange", () => {
  if (window.location.hash) {
    window.setTimeout(() => scrollToSection(window.location.hash, "auto"), 0);
  }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const requestType = data.get("type") || "Automation request";
  const business = data.get("business") || "Not provided";
  const phone = data.get("phone") || "Not provided";
  const subject = `${requestType} from ${data.get("name") || business}`;
  const body = [
    `Name: ${data.get("name")}`,
    `Business: ${business}`,
    `Email: ${data.get("email")}`,
    `Phone: ${phone}`,
    `Request type: ${requestType}`,
    `Date received: ${new Date().toLocaleString("en-US")}`,
    "",
    "Message",
    `${data.get("message")}`,
    "",
    "Admin note: copy this request into the local Requests panel.",
  ].join("\n");

  window.location.href = `mailto:mkhani.phd@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});

function initializePage() {
  if (pageInitialized) return;
  pageInitialized = true;

  if (window.lucide) {
    window.lucide.createIcons();
  }

  fitPanels();
  runIntroAnimation();

  if (window.location.hash) {
    window.setTimeout(() => scrollToSection(window.location.hash, "auto"), 100);
  }
}

window.setTimeout(initializePage, 0);
window.addEventListener("DOMContentLoaded", initializePage, { once: true });

window.addEventListener("load", fitPanels);
