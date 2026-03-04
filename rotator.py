import random
import socket
import threading
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

def forward(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

def handle_client(client_sock):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = client_sock.recv(4096)
            if not chunk:
                return
            request += chunk

        first_line = request.split(b"\r\n")[0].decode()
        method, path, _ = first_line.split(" ", 2)

        host, port, user, password = get_random_proxy()
        proxy_sock = socket.create_connection((host, int(port)), timeout=15)

        if method == "CONNECT":
            auth = f"{user}:{password}"
            import base64
            encoded = base64.b64encode(auth.encode()).decode()
            proxy_request = (
                f"CONNECT {path} HTTP/1.1\r\n"
                f"Host: {path}\r\n"
                f"Proxy-Authorization: Basic {encoded}\r\n\r\n"
            )
            proxy_sock.sendall(proxy_request.encode())
            resp = proxy_sock.recv(4096)
            if b"200" in resp:
                client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            else:
                client_sock.close()
                return
        else:
            auth = f"{user}:{password}"
            import base64
            encoded = base64.b64encode(auth.encode()).decode()
            lines = request.split(b"\r\n")
            lines.insert(1, f"Proxy-Authorization: Basic {encoded}".encode())
            request = b"\r\n".join(lines)
            proxy_sock.sendall(request)

        t1 = threading.Thread(target=forward, args=(client_sock, proxy_sock))
        t2 = threading.Thread(target=forward, args=(proxy_sock, client_sock))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    except Exception as e:
        print(f"Error: {e}")
        try: client_sock.close()
        except: pass

def main():
    port = int(os.environ.get("PORT", 8080))
    print(f"Loaded {len(PROXIES)} proxies")
    print(f"Rotating proxy running on port {port}...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(100)
    while True:
        client_sock, _ = server.accept()
        t = threading.Thread(target=handle_client, args=(client_sock,))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    main()
