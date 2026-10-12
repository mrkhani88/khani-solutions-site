"""Recreate the reviewed figure assets from locally downloaded original PDFs.

Usage: python3 scripts/extract_research_figures.py /path/to/original-pdfs
Requires PyMuPDF and Pillow; neither is required by build_portfolio.py.
PDF sources, SHA-256 hashes, native image references, pages and drawing crops
are recorded in content/research-media.json. No network calls are made.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import fitz
from PIL import Image

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('pdf_directory', type=Path)
args = parser.parse_args()
manifest = json.loads((root / 'scripts/content/research-media.json').read_text())
for group in manifest.values():
 for source in group.values():
  extraction = source['extraction']
  original = args.pdf_directory / extraction['file']
  if hashlib.sha256(original.read_bytes()).hexdigest() != source['sha256']:
   raise ValueError(f'Original PDF hash differs: {original.name}')
  with fitz.open(original) as doc:
   if 'xref' in extraction:
    image = Image.open(io.BytesIO(doc.extract_image(extraction['xref'])['image'])).convert('RGB')
   else:
    pix = doc[extraction['page'] - 1].get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=fitz.Rect(extraction['crop']))
    image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    if extraction['rotation']:
     image = image.rotate(extraction['rotation'], expand=True)
   image.thumbnail((1800, 1800))
   if image.size != (source['width'], source['height']):
    raise ValueError(f'Unexpected figure dimensions: {original.name}')
   image.save(root / source['asset'].lstrip('/'), 'WEBP', quality=94 if 'crop' in extraction else 92)
print('Recreated 17 reviewed PDF figure assets.')
