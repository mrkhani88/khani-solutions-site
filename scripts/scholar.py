"""Scholar presentation, backed by the same verified public snapshot as the client."""
from html import escape as e
from pathlib import Path
from datetime import datetime
import json
from scholar_sync import PROFILE_URL, validate
DATA = validate(json.loads((Path(__file__).resolve().parents[1] / 'assets/scholar/profile.json').read_text()))

def citation_link(cite, title):
 record = DATA['articles'].get(cite)
 if not record: return ''
 return f'<a class="text-link scholar-citation" data-scholar-paper="{e(cite)}" href="{e(record["cited_by_url"] or record["record_url"])}" target="_blank" rel="noopener" aria-label="View citations to {e(title)} on Google Scholar">Cited by {record["citations"]}{"*" if record["estimated"] else ""} ↗</a>'

def chart_bars():
 peak = max(p['citations'] for p in DATA['annual_citations']) or 1
 return ''.join(f'<li><button type="button" class="scholar-bar" data-scholar-year="{p["year"]}" data-citations="{p["citations"]}" aria-pressed="false" aria-label="{p["year"]}: {p["citations"]} citations"><span class="scholar-bar-count">{p["citations"]}</span><span class="scholar-bar-fill" style="--bar-height:{100*p["citations"]/peak:.3f}%"></span><span class="scholar-bar-year">{p["year"]}</span></button></li>' for p in DATA['annual_citations'])

def coauthor_rows():
 return ''.join(f'<li><a href="{e(p["url"])}" target="_blank" rel="noopener"><strong>{e(p["name"])}</strong><span>{e(p["affiliation"])}</span><span class="coauthor-arrow" aria-hidden="true">↗</span></a></li>' for p in DATA['coauthors'])

def scholar_section(link, compact=False):
 metrics = ''
 for key, title, definition in [('citations','Citations','Citations reported by Google Scholar'),('h_index','h-index','At least h publications with at least h citations each'),('i10_index','i10-index','Publications with at least 10 citations')]:
  m = DATA['metrics'][key]
  metrics += f'<article class="scholar-metric"><h3 title="{definition}">{title}</h3><div><strong data-scholar-metric="{key}" data-period="all">{m["all"]}</strong><span>All time</span></div><p><strong data-scholar-metric="{key}" data-period="recent">{m["recent"]}</strong><span data-scholar-recent-label>{e(DATA["recent_label"])}</span></p></article>'
 date = datetime.fromisoformat(DATA['checked_at']).strftime('%b %d, %Y')
 actions = link(PROFILE_URL,'Follow on Google Scholar','button scholar-follow')
 if compact: actions += '<a class="text-link" href="/AISolutions/publications.html#scholar-insights">Citation chart &amp; coauthors →</a>'
 body = f'<div class="scholar-heading"><div><p class="eyebrow">Research impact</p><h2>{"On Google Scholar." if compact else "Citations &amp; collaborators."}</h2></div><div class="actions">{actions}</div></div><p class="quiet scholar-follow-hint">Open my Scholar profile and select Follow for new articles and citation alerts.</p><div class="scholar-metrics">{metrics}</div>'
 if not compact:
  access = DATA['public_access']; access_html = ''
  if access:
   total = access['available']+access['not_available']; percent = 100*access['available']/total if total else 0
   access_html = f'<article class="scholar-access" data-scholar-access><p class="eyebrow">Open research</p><h3>Public access</h3><div class="scholar-access-counts"><div><strong data-scholar-available>{access["available"]}</strong><span>Available</span></div><div><strong data-scholar-unavailable>{access["not_available"]}{"*" if access["recused"] else ""}</strong><span>Not available</span></div></div><div class="scholar-access-bar" aria-hidden="true"><span data-scholar-access-fill style="width:{percent:.3f}%"></span></div><p class="quiet">Articles covered by funding mandates, as reported by Google Scholar.</p>{link(access["url"],"View public-access records","text-link scholar-access-link")}</article>'
  body += f'<div class="scholar-details"><article class="scholar-chart-card"><div class="scholar-chart-heading"><h3>Cited by year</h3><div class="scholar-periods" role="group" aria-label="Citation chart period"><button type="button" data-scholar-chart-period="all" aria-pressed="true">All shown</button><button type="button" data-scholar-chart-period="recent" aria-pressed="false">{e(DATA["recent_label"])}</button></div></div><div class="scholar-chart-scroll" tabindex="0" role="region" aria-label="Annual citation chart"><ol class="scholar-chart" data-scholar-chart>{chart_bars()}</ol></div><p class="quiet" data-scholar-chart-status role="status">Select a year to inspect its citation count. The current year is still in progress.</p></article>{access_html}</div><div class="scholar-coauthors"><h3>Coauthors on my Scholar profile</h3><ul data-scholar-coauthors>{coauthor_rows()}</ul></div>'
 body += f'<p class="scholar-freshness" data-scholar-freshness>Google Scholar · Checked <time data-scholar-checked datetime="{e(DATA["checked_at"])}">{date}</time> · Refreshes daily.</p>'
 anchor = '' if compact else 'id="scholar-insights"'
 return f'<section class="wrap section scholar-section {"scholar-compact" if compact else ""}" data-scholar-summary {anchor}>{body}</section>'
