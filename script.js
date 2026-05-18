const header = document.querySelector("[data-header]");
const nav = document.querySelector("[data-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const form = document.querySelector("[data-contact-form]");
const internalLinks = document.querySelectorAll('a[href^="#"]');

function updateHeader() {
  header.classList.toggle("is-scrolled", window.scrollY > 16);
}

window.addEventListener("scroll", updateHeader, { passive: true });
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

  if (window.location.hash) {
    window.setTimeout(() => scrollToSection(window.location.hash, "auto"), 100);
  }
});
