"""Independent battery thermal study; stage 01 is a verified 0D model."""
from pathlib import Path

def publish_pages(root):
    root=Path(root)
    for name in ['battery-thermal.html','battery-thermal-cad.html']:
        (root/'AISolutions'/name).write_text((root/'scripts/content'/name).read_text())

def battery_thermal_card():
    return '''<article class="simulation-card filter-item" id="battery-thermal" data-category="Thermal" data-method="systems" data-analysis-company-ids="independent-work"><div class="card-copy"><p class="eyebrow">Independent work / Battery thermal modeling</p><h2>Battery thermal modeling, step by step</h2><p>Start with one pouch cell: inspect heating and cooling, the governing energy balance, and the numerical checks. Later stages will add spatial conduction, the enclosure, PCB heating, and battery physics.</p><div class="pills"><span>FreeCAD</span><span>Python</span><span>SciPy</span><span>Open source</span></div><p class="study-note">Stage 01 available · 0D average temperature · Assumed inputs · Numerically verified, not experimentally validated.</p></div><a class="analysis-research-image" href="/AISolutions/battery-thermal.html" aria-label="Open the independent battery thermal modeling study"><img src="/assets/studies/battery-thermal/stage-01/figures/heating_cooling.png" alt="Single-cell average temperature rises under a one-watt heat input and cools after the heat source switches off" loading="lazy" width="2090" height="1330"></a><div class="card-bottom"><a class="text-link" href="/AISolutions/battery-thermal.html">Explore Stage 01 →</a><small>Independent Khani Solutions work</small></div></article>'''
