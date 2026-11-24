"""PCB thermal studies grouped with related Wisk work."""
from pathlib import Path

STAGE_07_VIDEO = "/assets/videos/portfolio/pcb-stage-07.mp4"
STAGE_07_POSTER = "/assets/studies/battery-thermal/stage-07/figures/adhesive_maps.png"
ICEPAK_VIDEO = "/assets/videos/portfolio/icepak-thermal-views.mp4"
ICEPAK_POSTER = "/assets/videos/portfolio/icepak-thermal-views.webp"


def stage_07_video():
    return f'''<div class="simulation-media"><video controls playsinline preload="none" width="1920" height="1080" style="display:block;width:100%;height:auto" poster="{STAGE_07_POSTER}" aria-label="Stage 07 battery and PCB heating and cooldown">
<source src="{STAGE_07_VIDEO}" type="video/mp4"><a href="{STAGE_07_VIDEO}">Open the Stage 07 video</a></video></div>'''


def stage_07_preview():
    return f'''<section class="card" aria-label="Stage 07 heating and cooldown video">
{stage_07_video()}
<p>Stage 07 · Inside the battery and PCB during heating and cooldown. This replay uses the saved 100 µm adhesive case.</p></section>'''

def icepak_video(preload="none"):
    return f'''<div class="simulation-media"><video controls playsinline preload="{preload}" width="1280" height="720" style="display:block;width:100%;height:auto" poster="{ICEPAK_POSTER}" aria-label="Icepak thermal field walkthrough across three saved views of one steady solution">
<source src="{ICEPAK_VIDEO}" type="video/mp4"><a href="{ICEPAK_VIDEO}">Open the Icepak video</a></video></div>'''

def publish_pages(root):
    root=Path(root)
    for name in ['battery-thermal-icepak.html','battery-thermal.html','battery-thermal-cad.html','battery-thermal-stage-02.html','battery-thermal-stage-03.html','battery-thermal-stage-04.html','battery-thermal-stage-05.html','battery-thermal-stage-06.html','battery-thermal-stage-07.html']:
        page = (root/'scripts/content'/name).read_text()
        if name in {'battery-thermal.html', 'battery-thermal-stage-07.html'}:
            page = page.replace('<!-- STAGE_07_PREVIEW -->', stage_07_preview(), 1)
        if name == 'battery-thermal-icepak.html':
            preview = '<section aria-label="Icepak thermal field walkthrough">' + icepak_video("metadata") + '</section>'
            page = page.replace('<section id="explorer">', preview + '<section id="explorer">', 1)
        (root/'AISolutions'/name).write_text(page)

def battery_thermal_card():
    return f'''<article class="simulation-card filter-item" id="battery-thermal" data-category="Thermal" data-method="systems" data-analysis-company-ids="wisk-experience">{stage_07_video()}<div class="card-copy"><p class="eyebrow">Wisk work / Battery thermal modeling</p><h2>Battery thermal modeling, step by step</h2><p>Start with one cell, then build a coupled PCB and enclosure model. The latest stage compares adhesive thicknesses under the largest graphite sheet, tracking cover and battery temperatures with a separate resistance-only diagnostic.</p><div class="pills"><span>FreeCAD</span><span>Python</span><span>SciPy</span><span>Open source</span></div><p class="study-note">Stages 01–07 available · Adhesive thickness and thermal coupling · Layered finite volumes and lumped packages · Assumed inputs · Numerically verified, not experimentally validated.</p></div><div class="card-bottom"><a class="text-link" href="/AISolutions/battery-thermal.html">Start with Stage 01 →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-02.html">Compare heat input →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-03.html">Explore PCB &amp; enclosure →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-04.html">Compare the RF cooling pad →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-05.html">Explore graphite spreading →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-06.html">Compare graphite sizes →</a><a class="text-link" href="/AISolutions/battery-thermal-stage-07.html">Compare adhesive thickness →</a></div></article>'''


def icepak_card():
    return f'''<article class="simulation-card filter-item" id="icepak-pcb" data-category="Thermal" data-method="cfd" data-analysis-company-ids="wisk-experience">{icepak_video()}<div class="card-copy"><p class="eyebrow">Wisk work / Icepak PCB thermal study</p><h2>Explore a smartphone’s thermal paths</h2><p>Inspect the corrected 5.5 W steady-conduction model: native battery, electronics and exterior contour views, selectable component statistics, mesh evidence and the original 15-page report.</p><div class="pills"><span>Ansys Icepak</span><span>Steady conduction</span><span>671,368 cells</span></div><p class="study-note">Illustrative assumptions · Saved volume maxima: battery 54.33 °C, processor 74.51 °C · Provisional results; heat balance, mesh independence and physical validation remain open. A separate model from the open-source stages.</p></div><a class="analysis-research-image" href="/AISolutions/battery-thermal-icepak.html#explorer" aria-label="Explore the corrected Icepak temperature maps"><img src="/assets/studies/battery-thermal/icepak-corrected-r1/images/Battery_Temperature_native.png" alt="Original saved Icepak battery temperature contour" loading="lazy" width="1800" height="1200"></a><div class="card-bottom"><a class="text-link" href="/AISolutions/battery-thermal-icepak.html#explorer">Interactive temperature views →</a><a class="text-link" href="/AISolutions/battery-thermal-icepak.html#downloads">Report, data &amp; native project →</a><a class="text-link" href="/AISolutions/battery-thermal.html">Open-source learning stages →</a></div></article>'''
