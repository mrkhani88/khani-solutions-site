"""Refresh only the public Scholar profile; keep the last verified snapshot on failure.

No search crawling, cookies, credentials, API keys, proxies or CAPTCHA handling.
The profile URL puts user= first as required by Scholar's robots.txt allowance.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen

PROFILE_ID = 'ipaKdZ4AAAAJ'
PROFILE_URL = f'https://scholar.google.com/citations?user={PROFILE_ID}&hl=en'
FETCH_URL = PROFILE_URL + '&pagesize=100'
OUTPUT = Path(__file__).resolve().parents[1] / 'assets/scholar/profile.json'
USER_AGENT = 'Mozilla/5.0 (compatible; KhaniSolutionsScholarSync/1.0; +https://khanisolutions.com)'
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
 def __init__(self, tag='', attrs=()):
  self.tag, self.attrs, self.children = tag, dict(attrs), []
 def text(self):
  return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())
 def find(self, tag=None, cls=None, id=None):
  result = []
  for child in self.children:
   if isinstance(child, Node):
    if (tag is None or child.tag == tag) and (cls is None or cls in child.attrs.get('class','').split()) and (id is None or child.attrs.get('id') == id): result.append(child)
    result.extend(child.find(tag, cls, id))
  return result
 def one(self, **selectors):
  nodes = self.find(**selectors)
  if len(nodes) != 1: raise ValueError(f'Expected one Scholar element: {selectors}, found {len(nodes)}')
  return nodes[0]

class Tree(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True); self.root = Node(); self.stack = [self.root]
 def handle_starttag(self, tag, attrs):
  n=Node(tag,attrs); self.stack[-1].children.append(n)
  if tag not in VOID:self.stack.append(n)
 def handle_endtag(self, tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag == tag:
    self.stack=self.stack[:i];break
 def handle_data(self, data):self.stack[-1].children.append(data)

def number(text):
 value = text.replace(',','').strip()
 if not re.fullmatch(r'\d+',value):raise ValueError(f'Invalid citation count: {text!r}')
 return int(value)

def public_link(href):
 url=urljoin('https://scholar.google.com',href)
 parts=urlparse(url)
 if parts.scheme!='https' or parts.netloc!='scholar.google.com' or parts.path not in ['/citations','/scholar']:raise ValueError('Unexpected Scholar link')
 return url

def parse_profile(html, checked_at=None):
 tree=Tree();tree.feed(html);root=tree.root
 name=root.one(id='gsc_prf_in').text()
 if name!='Mohammadreza Khani':raise ValueError('Profile identity does not match')
 table=root.one(id='gsc_rsb_st')
 header=table.one(tag='thead').find(tag='th')
 recent_label=header[-1].text()
 metrics={}
 for row in table.one(tag='tbody').find(tag='tr'):
  cells=row.find(tag='td'); label=cells[0].text()
  key={'Citations':'citations','h-index':'h_index','i10-index':'i10_index'}.get(label)
  if key:metrics[key]={'all':number(cells[1].text()),'recent':number(cells[2].text())}
 panel=root.one(id='gsc_rsb_cit')
 years=[number(n.text()) for n in panel.find(cls='gsc_g_t')]
 counts=[number(n.text()) for n in panel.find(cls='gsc_g_al')]
 if not years or len(years)!=len(counts):raise ValueError('Incomplete citation history')
 annual=[{'year':year,'citations':count} for year,count in zip(years,counts)]
 access_nodes=root.find(id='gsc_rsb_mnd');access=None
 if access_nodes:
  a=access_nodes[0];available=a.find(cls='gsc_rsb_m_a')[0].text();unavailable=a.find(cls='gsc_rsb_m_na')[0].text()
  access={'available':number(re.search(r'[\d,]+',available)[0]),'not_available':number(re.search(r'[\d,]+',unavailable)[0]),'recused':'*' in unavailable,'url':public_link(a.one(id='gsc_lwp_mndt_lnk').attrs['href'])}
 coauthors=[]
 for person in root.one(id='gsc_rsb_co').find(tag='li'):
  desc=person.one(cls='gsc_rsb_a_desc');anchor=desc.one(tag='a')
  affiliations=desc.find(cls='gsc_rsb_a_ext')
  coauthors.append({'name':anchor.text(),'affiliation':affiliations[0].text() if affiliations else '', 'url':public_link(anchor.attrs['href'])})
 articles={}
 for row in root.find(cls='gsc_a_tr'):
  title=row.one(cls='gsc_a_at');record=public_link(title.attrs['href']);citation=parse_qs(urlparse(record).query)['citation_for_view'][0]
  if not citation.startswith(PROFILE_ID+':'):raise ValueError('Unexpected publication profile')
  cell=row.one(cls='gsc_a_c');anchors=cell.find(tag='a');cited=next((a for a in anchors if 'gsc_a_ac' in a.attrs.get('class','').split()),None)
  count_text=cited.text() if cited else ''
  estimate='*' in count_text;count=number(count_text.replace('*','')) if count_text.replace('*','').strip() else 0
  articles[citation.split(':',1)[1]]={'citations':count,'estimated':estimate,'duplicate':bool(cited and 'gsc_a_acm' in cited.attrs.get('class','').split()),'cited_by_url':public_link(cited.attrs['href']) if cited and count else None,'record_url':record}
 data={'schema_version':1,'profile_id':PROFILE_ID,'profile_url':PROFILE_URL,'name':name,'checked_at':checked_at or datetime.now(timezone.utc).isoformat(timespec='seconds'),'recent_label':recent_label,'metrics':metrics,'annual_citations':annual,'public_access':access,'coauthors':coauthors,'articles':articles}
 validate(data);return data

def validate(data):
 if data.get('schema_version')!=1 or data.get('profile_id')!=PROFILE_ID or data.get('profile_url')!=PROFILE_URL:raise ValueError('Snapshot identity mismatch')
 if datetime.fromisoformat(data['checked_at']).tzinfo is None:raise ValueError('Snapshot timestamp needs a timezone')
 if not re.fullmatch(r'Since \d{4}',data['recent_label']):raise ValueError('Invalid recent-period label')
 for key in ['citations','h_index','i10_index']:
  metric=data['metrics'][key]
  if any(type(metric[k]) is not int or metric[k]<0 for k in ['all','recent']) or metric['recent']>metric['all']:raise ValueError('Invalid citation metrics')
 years=[p['year'] for p in data['annual_citations']]
 if any(type(y) is not int or not 1900<=y<=2200 for y in years):raise ValueError('Invalid chart years')
 if not years or years!=sorted(set(years)) or any(type(p['citations']) is not int or p['citations']<0 for p in data['annual_citations']):raise ValueError('Invalid yearly chart')
 if not data['articles']:raise ValueError('No article records returned')
 for cite, article in data['articles'].items():
  if not re.fullmatch(r'[A-Za-z0-9_-]+',cite) or type(article['citations']) is not int or article['citations']<0:raise ValueError('Invalid article count')
  public_link(article['record_url'])
  if article['cited_by_url']:public_link(article['cited_by_url'])
 for coauthor in data['coauthors']:public_link(coauthor['url'])
 if data['public_access']:
  public_link(data['public_access']['url'])
  for key in ['available','not_available']:
   if type(data['public_access'][key]) is not int or data['public_access'][key]<0:raise ValueError('Invalid public-access counts')
 return data

def robots_allow(text, url):
 """Use the longest matching Allow/Disallow rule, with Allow winning a tie."""
 groups=[]; agents=[]; rules=[]; has_rules=False
 for raw in text.splitlines():
  line=raw.split('#',1)[0].strip()
  if ':' not in line:continue
  key,value=(x.strip() for x in line.split(':',1));key=key.lower()
  if key=='user-agent':
   if has_rules:groups.append((agents,rules));agents=[];rules=[];has_rules=False
   agents.append(value.lower())
  elif key in ['allow','disallow'] and agents:
   rules.append((key,value));has_rules=True
 groups.append((agents,rules))
 applicable=[rules for agents,rules in groups if '*' in agents]
 if not applicable:raise ValueError('No general robots directives found')
 path=urlparse(url).path+'?'+urlparse(url).query;matches=[]
 for rules in applicable:
  for action,pattern in rules:
   if not pattern:continue
   regex='^'+re.escape(pattern).replace(r'\*','.*')
   if pattern.endswith('$'):regex=regex[:-2]+'$'
   if re.match(regex,path):matches.append((len(pattern.replace('*','')),action=='allow'))
 return max(matches,default=(0,True))[1]

def fetch(url):
 with urlopen(Request(url,headers={'User-Agent':USER_AGENT,'Accept-Language':'en'}),timeout=30) as response:
  body=response.read(2_000_001)
  if len(body)>2_000_000:raise ValueError('Unexpectedly large Scholar response')
  return body.decode('utf-8')

def refresh(output=OUTPUT, html_file=None, keep_last_good=False):
 try:
  if html_file:html=Path(html_file).read_text()
  else:
   robots=fetch('https://scholar.google.com/robots.txt')
   if not robots_allow(robots,FETCH_URL):raise ValueError('Profile refresh disallowed by robots.txt')
   html=fetch(FETCH_URL)
  data=parse_profile(html)
  output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
  tmp=output.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(output)
  print(f"Verified Scholar snapshot: {data['metrics']['citations']['all']} citations, {len(data['articles'])} article records, {len(data['coauthors'])} coauthors.")
  return True
 except Exception as error:
  if not keep_last_good:raise
  validate(json.loads(Path(output).read_text()))
  print(f'::warning::Scholar refresh unavailable ({type(error).__name__}); retained the last verified snapshot and its original timestamp.',file=sys.stderr)
  return False

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=OUTPUT)
 parser.add_argument('--html-file',type=Path,help='Parse an already retrieved anonymous public profile')
 parser.add_argument('--keep-last-good',action='store_true')
 args=parser.parse_args();refresh(args.output,args.html_file,args.keep_last_good)
