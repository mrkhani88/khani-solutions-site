"""Publish project ZIP links and keep browser entry points for their old URLs."""

from html import escape, unescape
import json
import re
from urllib.parse import unquote, urljoin, urlsplit


SITE_ORIGIN = 'https://khanisolutions.com'
HREF = re.compile(r'(?P<attr>(?<![\w:-])href\s*=\s*)(?P<quote>["\'])(?P<url>[^"\']*)(?P=quote)', re.IGNORECASE)


def rewrite_archive_links(markup, page_path, archives):
    def replace(match):
        href = unescape(match['url'])
        if '.zip' not in href.lower():
            return match[0]
        source = urlsplit(urljoin(SITE_ORIGIN + page_path, href))
        target = archives.get(unquote(source.path)) if source.hostname == 'khanisolutions.com' else None
        if target is None:
            return match[0]
        quote = match['quote']
        return f"{match['attr']}{quote}{escape(target, quote=True)}{quote}"

    return HREF.sub(replace, markup)


def finalize_archive_links(root):
    archives = json.loads((root / 'assets/study-downloads.json').read_text())
    for page in [root / 'index.html', *(root / 'AISolutions').glob('*.html')]:
        markup = page.read_text()
        updated = rewrite_archive_links(markup, '/' + page.relative_to(root).as_posix(), archives)
        if updated != markup:
            page.write_text(updated)

    for source, target in archives.items():
        redirect = root / source.lstrip('/') / 'index.html'
        redirect.parent.mkdir(parents=True, exist_ok=True)
        url = escape(target, quote=True)
        filename = escape(source.rsplit('/', 1)[-1])
        redirect.write_text(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={url}">
<title>Download {filename} | Khani Solutions</title>
</head>
<body>
<main><h1>Download {filename}</h1><p><a href="{url}">Download the ZIP on GitHub</a></p></main>
</body>
</html>
''')
