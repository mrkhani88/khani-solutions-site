const moduleTabs = [...document.querySelectorAll("[data-module-tab]")];
const modulePanels = [...document.querySelectorAll("[data-module-panel]")];
const menu = document.querySelector("[data-menu]");
const menuButton = document.querySelector("[data-menu-button]");

function setActiveModule(moduleName, options = {}) {
  const selectedTab = moduleTabs.find((tab) => tab.dataset.moduleTab === moduleName) || moduleTabs[0];
  if (!selectedTab) return;

  moduleTabs.forEach((tab) => {
    const isSelected = tab === selectedTab;
    tab.setAttribute("aria-selected", String(isSelected));
    tab.tabIndex = isSelected ? 0 : -1;
  });

  modulePanels.forEach((panel) => {
    const isSelected = panel.dataset.modulePanel === selectedTab.dataset.moduleTab;
    panel.hidden = !isSelected;
    panel.classList.toggle("is-active", isSelected);
  });

  if (options.updateHash !== false) {
    history.replaceState(null, "", `#${selectedTab.dataset.moduleTab}`);
  }

  if (options.focus) selectedTab.focus();
}

moduleTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setActiveModule(tab.dataset.moduleTab));
  tab.addEventListener("keydown", (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + moduleTabs.length) % moduleTabs.length;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % moduleTabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = moduleTabs.length - 1;
    setActiveModule(moduleTabs[nextIndex].dataset.moduleTab, { focus: true });
  });
});

function closeMenu() {
  menu?.classList.remove("is-open");
  menuButton?.setAttribute("aria-expanded", "false");
}

menuButton?.addEventListener("click", () => {
  const isOpen = menu?.classList.toggle("is-open") ?? false;
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

document.addEventListener("click", (event) => {
  if (!menu?.classList.contains("is-open")) return;
  if (event.target instanceof Element && event.target.closest("[data-header]")) return;
  closeMenu();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});

menu?.addEventListener("click", (event) => {
  if (event.target instanceof Element && event.target.closest("a")) closeMenu();
});

setActiveModule(window.location.hash.replace(/^#/, ""), { updateHash: false });
window.lucide?.createIcons();
window.addEventListener("load", () => window.lucide?.createIcons());
