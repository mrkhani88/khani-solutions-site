const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const form = document.querySelector("[data-contact-form]");
const internalLinks = document.querySelectorAll('a[href^="#"]');
const introLoader = document.querySelector("[data-intro-loader]");
const introLogo = document.querySelector("[data-intro-logo]");
const headerLogo = document.querySelector(".brand-mark");
const focalImages = document.querySelectorAll("[data-focal-x][data-focal-y]");
const feedScrollQuery = window.matchMedia("(prefers-reduced-motion: no-preference)");
let snapSections = [];
let feedScrollLocked = false;
let activePanelIndex = 0;
let touchStartX = 0;
let touchStartY = 0;
let touchStartIndex = 0;
let touchHasPanelIntent = false;
let fitTimer;
let pageInitialized = false;
let panelTransitionTimer;
let wheelGestureTimer;
let wheelGestureDelta = 0;
let wheelGestureConsumed = false;
let wheelSuppressUntil = 0;
const densityClasses = ["is-compact", "is-tight", "is-ultra"];
const wheelGestureResetMs = 280;
const wheelGestureThreshold = 80;
const panelTransitionMs = 780;
const wheelTransitionSuppressMs = 1050;

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
  header.classList.toggle("is-scrolled", feedModeActive() ? activePanelIndex > 0 : window.scrollY > 16);
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
  if (feedModeActive()) {
    const targetIndex = panelIndexFromHash(hash);
    if (targetIndex >= 0) {
      setActivePanel(targetIndex, { animate: behavior === "smooth", updateHash: false });
    }
    return;
  }
  document.documentElement.classList.add("is-jump-scroll");
  window.scrollTo({ top: target.offsetTop, behavior });
  window.setTimeout(() => document.documentElement.classList.remove("is-jump-scroll"), behavior === "smooth" ? 650 : 120);
}

function clearInitialSectionHash() {
  if (!window.location.hash) return;
  history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
  window.scrollTo({ top: 0, behavior: "auto" });
}

function panelOverflows(section) {
  return section.scrollHeight > section.clientHeight + 2 || section.scrollWidth > section.clientWidth + 2;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function focalPositionPercent(boxSize, renderedSize, focalRatio) {
  const cropSize = renderedSize - boxSize;
  if (cropSize <= 1) return 50;
  const offset = boxSize / 2 - renderedSize * focalRatio;
  return clamp((offset / (boxSize - renderedSize)) * 100, 0, 100);
}

function updateFocalImages() {
  focalImages.forEach((image) => {
    if (!(image instanceof HTMLImageElement) || !image.naturalWidth || !image.naturalHeight) return;
    const frame = image.closest(".contact-photo") || image.parentElement;
    const box = frame?.getBoundingClientRect();
    if (!box?.width || !box.height) return;

    const focalX = clamp(Number(image.dataset.focalX) || 0.5, 0.01, 0.99);
    const focalY = clamp(Number(image.dataset.focalY) || 0.5, 0.01, 0.99);
    const scale = Math.max(
      box.width / image.naturalWidth,
      box.height / image.naturalHeight,
      box.width / (2 * focalX * image.naturalWidth),
      box.width / (2 * (1 - focalX) * image.naturalWidth),
      box.height / (2 * focalY * image.naturalHeight),
      box.height / (2 * (1 - focalY) * image.naturalHeight),
    );
    const renderedWidth = image.naturalWidth * scale;
    const renderedHeight = image.naturalHeight * scale;
    const left = clamp(box.width / 2 - renderedWidth * focalX, box.width - renderedWidth, 0);
    const top = clamp(box.height / 2 - renderedHeight * focalY, box.height - renderedHeight, 0);

    image.style.width = `${renderedWidth.toFixed(2)}px`;
    image.style.height = `${renderedHeight.toFixed(2)}px`;
    image.style.left = `${left.toFixed(2)}px`;
    image.style.top = `${top.toFixed(2)}px`;
    image.style.objectPosition = `${focalPositionPercent(box.width, renderedWidth, focalX).toFixed(2)}% ${focalPositionPercent(box.height, renderedHeight, focalY).toFixed(2)}%`;
    image.dataset.focalReady = "true";
  });
}

function setupFocalImages() {
  focalImages.forEach((image) => {
    if (image instanceof HTMLImageElement) {
      image.addEventListener("load", updateFocalImages);
    }
  });
  updateFocalImages();
}

function refreshSnapSections() {
  snapSections = [...document.querySelectorAll(".snap-section")];
}

function feedModeActive() {
  return document.documentElement.classList.contains("feed-mode");
}

function panelHash(section) {
  if (!section) return "#top";
  return section.id === "top" ? "#top" : `#${section.id}`;
}

function panelIndexFromHash(hash) {
  refreshSnapSections();
  if (!hash || hash === "#top") return 0;
  return snapSections.findIndex((section) => `#${section.id}` === hash);
}

function syncPanelOffsets() {
  snapSections.forEach((section, index) => {
    section.style.setProperty("--panel-offset", `${(index - activePanelIndex) * 100}%`);
    section.style.setProperty("--panel-index", String(index));
    section.classList.toggle("is-active", index === activePanelIndex);
    section.setAttribute("aria-hidden", index === activePanelIndex ? "false" : "true");
  });
  document.documentElement.style.setProperty("--active-panel", String(activePanelIndex));
}

function setActivePanel(index, options = {}) {
  refreshSnapSections();
  if (!snapSections.length) return;

  const nextIndex = Math.max(0, Math.min(snapSections.length - 1, index));
  const shouldAnimate = options.animate !== false && nextIndex !== activePanelIndex;
  activePanelIndex = nextIndex;

  window.clearTimeout(panelTransitionTimer);
  document.documentElement.classList.toggle("feed-instant", !shouldAnimate);
  document.documentElement.classList.toggle("is-panel-transitioning", shouldAnimate);
  feedScrollLocked = shouldAnimate;
  syncPanelOffsets();
  updateHeader();

  if (options.updateHash) {
    history.pushState(null, "", panelHash(snapSections[activePanelIndex]));
  } else if (options.replaceHash) {
    history.replaceState(null, "", panelHash(snapSections[activePanelIndex]));
  }

  if (shouldAnimate) {
    panelTransitionTimer = window.setTimeout(() => {
      feedScrollLocked = false;
      document.documentElement.classList.remove("is-panel-transitioning");
    }, panelTransitionMs);
  } else {
    window.requestAnimationFrame(() => document.documentElement.classList.remove("feed-instant", "is-panel-transitioning"));
    feedScrollLocked = false;
  }
}

function setupFeedMode() {
  refreshSnapSections();
  const shouldUseFeedMode = feedScrollEnabled();
  document.documentElement.classList.toggle("feed-mode", shouldUseFeedMode);
  document.body.classList.toggle("feed-mode", shouldUseFeedMode);
  activePanelIndex = Math.max(0, panelIndexFromHash(window.location.hash));

  if (shouldUseFeedMode) {
    window.scrollTo({ top: 0, behavior: "auto" });
    setActivePanel(activePanelIndex, { animate: false });
  } else {
    snapSections.forEach((section) => {
      section.classList.remove("is-active");
      section.removeAttribute("aria-hidden");
      section.style.removeProperty("--panel-offset");
      section.style.removeProperty("--panel-index");
    });
  }
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
  updateFocalImages();
  if (feedModeActive()) {
    syncPanelOffsets();
  }
}

function scheduleFitPanels() {
  window.clearTimeout(fitTimer);
  fitTimer = window.setTimeout(fitPanels, 80);
}

function currentSnapIndex() {
  if (feedModeActive()) return activePanelIndex;
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
  if (feedModeActive()) {
    setActivePanel(nextIndex, { animate: true, replaceHash: true });
    return;
  }
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
    if (
      !feedScrollEnabled() ||
      isEditableTarget(event.target) ||
      Math.abs(event.deltaY) <= Math.abs(event.deltaX) ||
      Math.abs(event.deltaY) < 3
    ) {
      return;
    }
    const now = performance.now();
    const direction = event.deltaY > 0 ? 1 : -1;
    if (!feedModeActive() && sectionCanScroll(event, direction)) return;
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
    if (feedModeActive()) {
      setActivePanel(snapSections.length - 1, { animate: true, replaceHash: true });
    } else {
      snapSections[snapSections.length - 1]?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
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

window.addEventListener("popstate", () => {
  if (feedModeActive()) {
    window.setTimeout(() => scrollToSection(window.location.hash || "#top", "auto"), 0);
  }
});

feedScrollQuery.addEventListener?.("change", () => {
  setupFeedMode();
  fitPanels();
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

  clearInitialSectionHash();
  setupFeedMode();
  setupFocalImages();
  fitPanels();
  runIntroAnimation();

  if (window.location.hash && !feedModeActive()) {
    window.setTimeout(() => scrollToSection(window.location.hash, "auto"), 100);
  }
}

window.setTimeout(initializePage, 0);
window.addEventListener("DOMContentLoaded", initializePage, { once: true });

window.addEventListener("load", fitPanels);

window.KhaniFeed = {
  currentIndex: () => activePanelIndex,
  goTo: (index, options = {}) => setActivePanel(index, options),
};
window.fitPanels = fitPanels;
window.centerFocalImages = updateFocalImages;
