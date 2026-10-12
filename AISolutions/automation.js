'use strict';
const examples = {
  leads: { title: 'From inquiry to next step.', message: 'I would like to simplify website inquiries and customer follow-ups.', steps: [['↗', 'A customer reaches out', 'Your website captures the details.'], ['✦', 'AI prepares the response', 'A draft based on your services.'], ['✓', 'Your team takes it from here', 'Review, respond and follow up.']] },
  paperwork: { title: 'From paperwork to organized records.', message: 'I would like help automating documents and everyday paperwork.', steps: [['↗', 'A document arrives', 'An invoice, form or email attachment.'], ['✦', 'AI extracts and organizes', 'Key details prepared for your records.'], ['✓', 'Your team checks the details', 'Approve before updating your system.']] },
  bookings: { title: 'From booking to follow-up.', message: 'I would like to simplify booking, reminders and customer follow-ups.', steps: [['↗', 'A customer requests a time', 'Your booking form collects preferences.'], ['✦', 'Your calendar connects the steps', 'Confirmed bookings trigger reminders.'], ['✓', 'Your team stays in control', 'Approve changes and review follow-ups.']] },
  knowledge: { title: 'From a question to a useful answer.', message: 'I would like an internal AI assistant for our business documents and team knowledge.', steps: [['↗', 'A team member asks a question', 'How does our process work?'], ['✦', 'AI searches approved documents', 'A draft answer with source references.'], ['✓', 'Your team verifies the answer', 'Check the source before acting.']] },
  reporting: { title: 'From scattered data to a clear view.', message: 'I would like a dashboard that brings our business information together.', steps: [['↗', 'Connect your agreed data sources', 'Spreadsheets and business systems.'], ['✦', 'Bring the numbers together', 'A clear dashboard and draft summary.'], ['✓', 'Your team reviews the picture', 'Verify the data and decide next steps.']] },
  quotes: { title: 'From request to a reviewed quote.', message: 'I would like to simplify preparing quotes and invoices.', steps: [['↗', 'A customer describes the job', 'Collect scope and requirements.'], ['✦', 'Prepare a draft quote', 'Use your agreed pricing and templates.'], ['✓', 'You approve before sending', 'Review the scope, price and terms.']] }
};
let selectedExample = 'leads';
const menu = document.querySelector('.menu-toggle');
const nav = document.querySelector('#automation-nav');
menu.addEventListener('click', () => {
  const open = menu.getAttribute('aria-expanded') !== 'true';
  menu.setAttribute('aria-expanded', String(open)); nav.classList.toggle('is-open', open);
});
nav.addEventListener('click', event => {
  if (event.target.closest('a')) { menu.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); }
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && nav.classList.contains('is-open')) { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.focus(); }
});
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  selectedExample = button.dataset.example;
  const example = examples[selectedExample];
  document.querySelector('#example-title').textContent = example.title;
  const list = document.querySelector('#example-steps'); list.replaceChildren();
  for (const [symbol, title, description] of example.steps) {
    const li = document.createElement('li'); const icon = document.createElement('span'); icon.className = 'step-icon'; icon.setAttribute('aria-hidden', 'true'); icon.textContent = symbol;
    const copy = document.createElement('div'); const strong = document.createElement('strong'); strong.textContent = title; const text = document.createElement('span'); text.textContent = description; copy.append(strong, text); li.append(icon, copy); list.append(li);
  }
  document.querySelectorAll('.example-picker [data-example]').forEach(tab => tab.setAttribute('aria-pressed', String(tab.dataset.example === selectedExample)));
  if (!button.closest('.example-picker')) document.querySelector('#examples').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
}));
document.querySelector('#example-cta').addEventListener('click', () => {
  const message = document.querySelector('[name="message"]');
  if (!message.value.trim()) message.value = examples[selectedExample].message;
});
document.querySelector('#automation-contact').addEventListener('submit', event => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const body = `Name: ${data.get('name')}\nEmail: ${data.get('email')}\nBusiness / town: ${data.get('business') || 'Not provided'}\n\n${data.get('message')}`;
  const url = `mailto:mkhani.phd@gmail.com?subject=${encodeURIComponent('AI automation inquiry — Khani Solutions')}&body=${encodeURIComponent(body)}`;
  document.querySelector('#form-status').textContent = 'Your email draft is ready. Review and send it in your email app, or email mkhani.phd@gmail.com directly.';
  window.location.href = url;
});
if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('arrive'); observer.unobserve(entry.target); } }), { threshold: 0.12 });
  document.querySelectorAll('.service, .workflow-demo, .start-steps article, .region').forEach(element => observer.observe(element));
}
