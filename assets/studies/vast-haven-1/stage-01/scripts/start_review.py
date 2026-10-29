from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
B=Path(__file__).resolve().parents[1]
print('Local CAD review: http://127.0.0.1:8893/review/Review.html',flush=True)
print('Keep this process running while reviewing; Ctrl-C stops it.',flush=True)
ThreadingHTTPServer(('127.0.0.1',8893),partial(SimpleHTTPRequestHandler,directory=str(B))).serve_forever()
