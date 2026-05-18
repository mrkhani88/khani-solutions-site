const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const form = document.querySelector("[data-contact-form]");
const internalLinks = document.querySelectorAll('a[href^="#"]');
const snapSections = [...document.querySelectorAll(".snap-section")];
const phoneFeedQuery = window.matchMedia("(max-width: 900px) and (prefers-reduced-motion: no-preference)");
let feedScrollLocked = false;
let fitTimer;
const densityClasses = ["is-compact", "is-tight", "is-ultra"];

function updateHeader() {
  header.classList.toggle("is-scrolled", window.scrollY > 16);
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
    nav.classList.remove("is-open");
    header.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
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

function fitPanels() {
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
  const anchor = window.scrollY + window.innerHeight * 0.42;
  return snapSections.reduce((closestIndex, section, index) => {
    const closestDistance = Math.abs(snapSections[closestIndex].offsetTop - anchor);
    const distance = Math.abs(section.offsetTop - anchor);
    return distance < closestDistance ? index : closestIndex;
  }, 0);
}

function scrollFeed(direction) {
  if (!phoneFeedQuery.matches || feedScrollLocked) return;
  const nextIndex = Math.max(0, Math.min(snapSections.length - 1, currentSnapIndex() + direction));
  const target = snapSections[nextIndex];
  if (!target) return;
  feedScrollLocked = true;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => {
    feedScrollLocked = false;
  }, 720);
}

function sectionCanScroll(event, direction) {
  const section = event.target instanceof Element ? event.target.closest(".snap-section") : null;
  if (!section || section.scrollHeight <= section.clientHeight + 2) return false;
  const atTop = section.scrollTop <= 2;
  const atBottom = section.scrollTop + section.clientHeight >= section.scrollHeight - 2;
  return direction > 0 ? !atBottom : !atTop;
}

window.addEventListener(
  "wheel",
  (event) => {
    if (!phoneFeedQuery.matches || Math.abs(event.deltaY) <= Math.abs(event.deltaX) || Math.abs(event.deltaY) < 18) return;
    if (sectionCanScroll(event, event.deltaY > 0 ? 1 : -1)) return;
    event.preventDefault();
    scrollFeed(event.deltaY > 0 ? 1 : -1);
  },
  { passive: false },
);

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
  const subject = `${data.get("type") || "Automation request"} from ${data.get("business") || "local business"}`;
  const body = [
    `Name: ${data.get("name")}`,
    `Business: ${data.get("business")}`,
    `Email: ${data.get("email")}`,
    `Phone: ${data.get("phone") || "Not provided"}`,
    `Request type: ${data.get("type")}`,
    `Date received: ${new Date().toLocaleString("en-US")}`,
    "",
    "What should we automate first?",
    `${data.get("message")}`,
    "",
    "Admin note: copy this request into the local Requests panel.",
  ].join("\n");

  window.location.href = `mailto:mkhani.phd@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});

window.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  fitPanels();

  if (window.location.hash) {
    window.setTimeout(() => scrollToSection(window.location.hash, "auto"), 100);
  }
});

window.addEventListener("load", fitPanels);
