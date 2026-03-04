import random
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os

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

def fetch_via_proxy(url):
    host, port, user, password = get_random_proxy()
    proxy_handler = urllib.request.ProxyHandler({
        "http": f"http://{user}:{password}@{host}:{port}",
        "https": f"http://{user}:{password}@{host}:{port}",
    })
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = opener.open(req, timeout=15)
    return resp.read(), resp.status, dict(resp.headers)

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/fetch":
            if "url" not in params:
                self._respond(400, b"Missing ?url= parameter")
                return
            target_url = params["url"][0]
            try:
                body, status, headers = fetch_via_proxy(target_url)
                self.send_response(status)
                for k, v in headers.items():
                    if k.lower() in ("content-type",):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._respond(502, f"Error: {str(e)}".encode())

        elif parsed.path == "/ip":
            try:
                body, _, _ = fetch_via_proxy("https://api.ipify.org?format=json")
                self._respond(200, body)
            except Exception as e:
                self._respond(502, f"Error: {str(e)}".encode())

        elif parsed.path == "/":
            self._respond(200, f"Rotating proxy is live. {len(PROXIES)} proxies loaded.".encode())

        else:
            self._respond(404, b"Not found")

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Loaded {len(PROXIES)} proxies")
    print(f"API running on port {port}...")
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    server.serve_forever()
```

6. Click **"Commit changes"**

---

Render will **automatically redeploy** once you commit. Wait ~2 minutes for it to go live again, then we'll test with:
```
https://rotating-proxy-vt2c.onrender.com/ip
