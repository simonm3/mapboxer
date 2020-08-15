from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread


def start_server():
    """ fileserver to enable web page to access local files e.g. base.css """

    def target():
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args, **kwargs):
                pass

        handler = partial(Handler, directory=Path(__file__).parent)
        s = HTTPServer(("", 8000), handler)
        s.serve_forever()

    t = Thread(target=target, daemon=True)
    t.start()
