import random
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PROXY_FILE = "proxies.txt"

def load_proxies():
    with open(PROXY_FILE) as f:
        lines = [l.strip() for l in f if l.strip()]
    proxies = []
    for line in lines:
        parts = line.split(":")
        if len(parts) == 4:
            host, port, user, password = parts
            proxies.append((host, port, user, password))
    return proxies

PROXIES = load_proxies()

def get_random_proxy():
    return random.choice(PROXIES)

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def do_CONNECT(self):
        host, port, user, password = get_random_proxy()
        self.send_response(200, "Connection Established")
        self.end_headers()

    def _forward(self):
        host, port, user, password = get_random_proxy()
        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://{user}:{password}@{host}:{port}",
            "https": f"http://{user}:{password}@{host}:{port}",
        })
        opener = urllib.request.build_opener(proxy_handler)
        try:
            req = urllib.request.Request(self.path, headers=dict(self.headers))
            resp = opener.open(req, timeout=15)
            self.send_response(resp.status)
            for key, val in resp.headers.items():
                self.send_header(key, val)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, str(e))

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"Loaded {len(PROXIES)} proxies")
    print("Rotating proxy running on port 8080...")
    server = HTTPServer(("0.0.0.0", 8080), ProxyHandler)
    server.serve_forever()
