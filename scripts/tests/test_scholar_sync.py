import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scholar_sync as s

class ScholarSyncTests(unittest.TestCase):
 def setUp(self):self.data=json.loads(s.OUTPUT.read_text())
 def test_valid_snapshot(self):self.assertEqual(s.validate(self.data)['profile_id'],s.PROFILE_ID)
 def test_bad_counts_and_links_are_rejected(self):
  for mutate in [lambda d:d['metrics']['citations'].update(recent=d['metrics']['citations']['all']+1),lambda d:next(iter(d['articles'].values())).update(citations=-1),lambda d:d['coauthors'][0].update(url='https://example.com'),lambda d:d.update(checked_at='2026-10-12T00:00:00'),lambda d:d['annual_citations'].reverse()]:
   with self.subTest(mutate=mutate):
    data=copy.deepcopy(self.data);mutate(data)
    with self.assertRaises(ValueError):s.validate(data)
 def test_blocked_or_changed_response_keeps_cache_and_timestamp(self):
  for response in ['<html>CAPTCHA</html>','<div id="gsc_prf_in">Someone Else</div>']:
   with tempfile.TemporaryDirectory() as directory:
    output=Path(directory)/'profile.json';original=json.dumps(self.data).encode();output.write_bytes(original)
    source=Path(directory)/'response.html';source.write_text(response)
    self.assertFalse(s.refresh(output,source,True));self.assertEqual(output.read_bytes(),original)
 def test_network_failure_keeps_cache(self):
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'profile.json';original=json.dumps(self.data).encode();output.write_bytes(original)
   with patch.object(s,'fetch',side_effect=TimeoutError):self.assertFalse(s.refresh(output,keep_last_good=True))
   self.assertEqual(output.read_bytes(),original)
 def test_robots_allow_profile_but_not_search_or_pagination(self):
  robots='User-agent: *\nDisallow: /scholar\nDisallow: /citations?\nAllow: /citations?user=\nDisallow: /citations?*cstart=\n'
  self.assertTrue(s.robots_allow(robots,s.FETCH_URL))
  self.assertFalse(s.robots_allow(robots,s.FETCH_URL+'&cstart=20'))
  self.assertFalse(s.robots_allow(robots,'https://scholar.google.com/scholar?q=test'))
  self.assertFalse(s.robots_allow(robots,'https://scholar.google.com/citations?hl=en&user='+s.PROFILE_ID))
 def test_public_links_cannot_escape_scholar(self):
  for url in ['javascript:alert(1)','https://scholar.google.com.evil.test/citations','https://scholar.google.com/other','http://scholar.google.com/citations']:
   with self.assertRaises(ValueError):s.public_link(url)

if __name__=='__main__':unittest.main()
