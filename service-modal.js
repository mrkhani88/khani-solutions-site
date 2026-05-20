const serviceModalDetails = {
  calls: {
    title: "Calls",
    description: "AI phone intake for missed calls, simple questions, and routing.",
    what: "A business phone assistant that can answer common questions, collect caller details, and send the right information to you or your team.",
    how: "We map your common call types, write the response flow, connect it to your phone or intake process, and send summaries by email or dashboard.",
    help: "Fewer missed leads, faster first response, cleaner notes, and less time spent repeating the same phone explanations.",
  },
  texts: {
    title: "Texts",
    description: "Fast customer replies and follow-up by SMS.",
    what: "A text workflow that answers basic questions, confirms details, follows up with leads, and keeps conversations organized.",
    how: "We create approved reply patterns, connect them to your intake or calendar workflow, and keep handoff rules clear for anything sensitive.",
    help: "Customers get answers quickly, leads do not go cold, and your team spends less time typing the same replies.",
  },
  email: {
    title: "Email",
    description: "AI-assisted email drafting, sorting, and response workflows.",
    what: "A workflow that can classify incoming email, draft replies, pull out action items, and prepare follow-up messages.",
    how: "We define safe reply rules, business tone, categories, and approval steps so important messages stay under your control.",
    help: "Cleaner inboxes, faster replies, fewer forgotten requests, and less admin time spent reading repetitive messages.",
  },
  invoices: {
    title: "Invoices",
    description: "Invoice sending, reminders, and payment follow-up.",
    what: "A billing support workflow that prepares invoice messages, sends reminders, and tracks who needs follow-up.",
    how: "We connect your invoice process to templates, due-date reminders, customer records, and a simple follow-up list.",
    help: "Less manual chasing, more consistent billing, and clearer visibility into unpaid or delayed invoices.",
  },
  schedule: {
    title: "Schedule",
    description: "Booking, rescheduling, reminders, and calendar cleanup.",
    what: "A scheduling assistant that helps customers find times, reschedule appointments, and receive reminders.",
    how: "We connect your calendar rules, availability, service types, and reminder timing into one repeatable process.",
    help: "Fewer back-and-forth messages, fewer no-shows, and a cleaner calendar for the business owner.",
  },
  leads: {
    title: "Leads",
    description: "Lead capture, qualification, and next-step routing.",
    what: "A lead workflow that captures contact info, asks the right questions, scores urgency, and moves people to the next step.",
    how: "We build intake questions around your business, then route each lead to email, phone, calendar, or a request tracker.",
    help: "You respond to serious customers faster and avoid losing people who contacted you after hours.",
  },
  website: {
    title: "Website",
    description: "Simple business websites that connect to automation.",
    what: "A practical website or page update that explains your services, collects requests, and connects to your follow-up process.",
    how: "We write the page, design the layout, connect forms or email flows, and keep it easy to update as the business changes.",
    help: "Your website becomes part of operations, not just a brochure. Customers can understand, contact, and request service quickly.",
  },
  listings: {
    title: "Listings",
    description: "Google, Apple, and business profile cleanup.",
    what: "A local listing workflow for business hours, service details, photos, contact links, and basic profile consistency.",
    how: "We review public profiles, prepare corrections, organize business details, and help keep listings aligned across platforms.",
    help: "Customers find the right phone, address, hours, and service information with less confusion.",
  },
  reviews: {
    title: "Reviews",
    description: "Review requests, tracking, and response preparation.",
    what: "A workflow that asks happy customers for reviews, tracks new reviews, and drafts professional responses.",
    how: "We build timing rules, message templates, and a simple review log so requests happen consistently.",
    help: "More local trust, better online presence, and fewer missed chances to turn good work into public proof.",
  },
  reports: {
    title: "Reports",
    description: "Weekly summaries of activity, requests, and follow-up.",
    what: "A report workflow that summarizes calls, messages, requests, leads, tasks, invoices, and open follow-ups.",
    how: "We decide what matters to the business, pull it into a simple weekly view, and highlight what needs attention.",
    help: "You see what happened, what is stuck, and what should be improved without digging through every tool.",
  },
};

const serviceModal = document.querySelector("[data-service-modal]");
const serviceModalPanel = document.querySelector(".service-modal__panel");
const serviceModalTitle = document.querySelector("#service-modal-title");
const serviceModalDescription = document.querySelector("#service-modal-description");
const serviceModalWhat = document.querySelector("[data-service-what]");
const serviceModalHow = document.querySelector("[data-service-how]");
const serviceModalHelp = document.querySelector("[data-service-help]");

function openServiceModal(serviceKey) {
  const detail = serviceModalDetails[serviceKey];
  if (!detail || !serviceModal) return;
  serviceModalTitle.textContent = detail.title;
  serviceModalDescription.textContent = detail.description;
  serviceModalWhat.textContent = detail.what;
  serviceModalHow.textContent = detail.how;
  serviceModalHelp.textContent = detail.help;
  serviceModal.hidden = false;
  window.requestAnimationFrame(() => serviceModalPanel?.focus?.());
}

function closeServiceModal() {
  if (serviceModal) serviceModal.hidden = true;
}

document.querySelectorAll("[data-service]").forEach((tile) => {
  tile.addEventListener("click", () => openServiceModal(tile.dataset.service));
  tile.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openServiceModal(tile.dataset.service);
  });
});

document.querySelectorAll("[data-service-close]").forEach((control) => {
  control.addEventListener("click", closeServiceModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && serviceModal && !serviceModal.hidden) {
    event.preventDefault();
    closeServiceModal();
  }
});
