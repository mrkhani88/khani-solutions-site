const intro = document.querySelector('[data-logo-intro]');
const skip = document.querySelector('[data-skip-intro]');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
let timer;
let startedAt;
let completedAt;
const stage = intro.querySelector('.intro-stage');
const brandLogo = document.querySelector('.brand img');
function alignLogoDestination() {
  const box = stage.getBoundingClientRect();
  const destination = brandLogo.getBoundingClientRect();
  // Preserve the original cropped preview framing with a full-square SVG,
  // then match the exact rendered header image instead of fixed coordinates.
  const unit = Math.min(box.width / 755, box.height / 900);
  const size = 1254 * unit;
  const left = (box.width - 755 * unit) / 2 - 250 * unit;
  const top = (box.height - 900 * unit) / 2 - 155 * unit;
  const scale = destination.width / size;
  for (const [name, value] of Object.entries({
    'art-size': `${size}px`, 'art-left': `${left}px`, 'art-top': `${top}px`,
    'dock-x': `${destination.left - box.left - left}px`,
    'dock-y': `${destination.top - box.top - top}px`,
    'dock-scale': String(scale),
    'dock-radius': `${parseFloat(getComputedStyle(brandLogo).borderRadius) / scale}px`
  })) intro.style.setProperty(`--${name}`, value);
}
window.addEventListener('resize', alignLogoDestination);
function finishIntro() {
  clearTimeout(timer);
  intro.classList.remove('is-playing');
  intro.classList.add('is-complete');
  document.body.classList.remove('is-introducing');
  for (const element of document.querySelectorAll('.skip-link,main,header,footer')) element.inert = false;
  completedAt = performance.now();
  intro.dataset.elapsed = String(Math.round(completedAt - startedAt));
  if (intro.contains(document.activeElement)) document.querySelector('.brand').focus({preventScroll:true});
}
function playIntro() {
  clearTimeout(timer);
  intro.classList.remove('is-playing','is-complete');
  intro.hidden = false;
  void intro.offsetWidth;
  document.body.classList.add('is-introducing');
  for (const element of document.querySelectorAll('.skip-link,main,header,footer')) element.inert = true;
  alignLogoDestination();
  intro.classList.add('is-playing');
  startedAt = performance.now();
  completedAt = undefined;
  timer = setTimeout(finishIntro,reducedMotion.matches ? 500 : 5000);

}
skip.addEventListener('click',finishIntro);
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!intro.classList.contains('is-complete'))finishIntro();});
reducedMotion.addEventListener('change',()=>{if(reducedMotion.matches)finishIntro();});
if (isFirstPortfolioVisit) {
  // Decode the existing artwork before starting the five-second timeline.
  const logoImage = new Image();
  logoImage.src = '/assets/khani-solutions-logo.png';
  logoImage.decode().catch(()=>{}).then(playIntro);
} else {
  // Keep Overview immediately usable when returning from another page.
  intro.classList.add('is-complete');
  intro.dataset.skipped = 'already-open';
}
