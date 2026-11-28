#!/usr/bin/env python3
"""سيرفر «بالعشرة» — يعرض اللعبة ويربط الشاشة بجوال الحكم على نفس الواي فاي.

التشغيل:  python3 server.py
ثم افتح على هذا الجهاز:  http://localhost:8765
"""
import json, os, secrets, socket, sys, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
HERE = os.path.dirname(os.path.abspath(__file__))
ref_seen = {}                           # جوال الحكم ← آخر وقت سأل فيه عن الحالة
KEY = secrets.token_urlsafe(9)          # مفتاح الجلسة: بدونه ما أحد يقدر يتحكم
LOOPBACK = ("127.0.0.1", "::1", "::ffff:127.0.0.1")

lock = threading.Lock()
state = b"null"                          # آخر حالة أرسلتها الشاشة
cmds = []                                # أوامر الحكم بانتظار الشاشة

# سجل الأسئلة اللي انلعبت، محفوظ لكل جهاز حسب عنوان IP ماله: { "ip": { "معرّف الفئة": ["عنوان السؤال", ...] } }
PLAYED_FILE = os.path.join(HERE, "data", "played.json")


def client_ip(addr):
    ip = addr[7:] if addr.startswith("::ffff:") else addr
    return "127.0.0.1" if ip == "::1" else ip


def load_played():
    try:
        with open(PLAYED_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_played(d):
    os.makedirs(os.path.dirname(PLAYED_FILE), exist_ok=True)
    tmp = PLAYED_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PLAYED_FILE)


def clean_hist(h):
    """يقبل بس { نص: [نصوص] } وبحجم معقول."""
    out = {}
    if isinstance(h, dict):
        for k, v in list(h.items())[:500]:
            if isinstance(k, str) and isinstance(v, list):
                out[k[:40]] = [x[:300] for x in v if isinstance(x, str)][:1000]
    return out


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # ما يرسل شي فعلياً، بس يحدد كرت الشبكة
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def parts(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        return u.path, q.get("k", [""])[0], self.client_address[0] in LOOPBACK

    def body(self, limit):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if 0 < n <= limit else None

    def do_GET(self):
        global cmds
        path, k, local = self.parts()
        if path in ("/", "/fazaa.html"):
            with open(os.path.join(HERE, "fazaa.html"), "rb") as f:
                return self.send(200, f.read(), "text/html")
        if path == "/bank.js":             # بنك الأسئلة (ملف مستقل عن كود اللعبة)
            with open(os.path.join(HERE, "bank.js"), "rb") as f:
                return self.send(200, f.read(), "application/javascript")
        if path == "/played":              # سجل هذا الجهاز (حسب IP)
            ip = client_ip(self.client_address[0])
            with lock:
                hist = load_played().get(ip, {})
            return self.send(200, json.dumps({"ip": ip, "hist": hist}, ensure_ascii=False).encode())
        if path == "/info" and local:      # للشاشة فقط (نفس الجهاز)
            url = "http://%s:%d/?ref=%s" % (lan_ip(), PORT, KEY)
            now = time.time()
            with lock:
                refs = sum(1 for t in ref_seen.values() if now - t < 4)   # جوالات حكم سألت عن الحالة آخر ٤ ثواني
            return self.send(200, json.dumps({"key": KEY, "url": url, "refs": refs}).encode())
        if not secrets.compare_digest(k, KEY):
            return self.send(403)
        if path == "/state":
            with lock:
                if not local:
                    ref_seen[self.client_address[0]] = time.time()
                return self.send(200, state)
        if path == "/cmds" and local:
            with lock:
                out, cmds = cmds, []
            return self.send(200, json.dumps(out).encode())
        self.send(404)

    def do_POST(self):
        global state, KEY
        path, k, local = self.parts()
        if path == "/rekey" and local:     # لعبة جديدة: مفتاح جديد، فجوالات الحكام القدام تنفصل
            with lock:
                KEY = secrets.token_urlsafe(9)
                ref_seen.clear()
            return self.send(204)
        if path == "/played":              # كل جهاز يكتب سجله هو بس (المفتاح عنوانه)
            b = self.body(200_000)
            try:
                hist = clean_hist(json.loads(b).get("hist"))
            except Exception:
                return self.send(400)
            ip = client_ip(self.client_address[0])
            with lock:
                d = load_played()
                if hist:
                    d[ip] = hist
                else:
                    d.pop(ip, None)
                save_played(d)
            return self.send(204)
        if not secrets.compare_digest(k, KEY):
            return self.send(403)
        if path == "/state" and local:
            b = self.body(200_000)
            if b is None:
                return self.send(400)
            with lock:
                state = b
            return self.send(204)
        if path == "/cmd":
            b = self.body(1000)
            try:
                c = json.loads(b)
                assert isinstance(c, dict)
            except Exception:
                return self.send(400)
            with lock:
                if len(cmds) < 50:
                    cmds.append(c)
            return self.send(204)
        self.send(404)


if __name__ == "__main__":
    print("بالعشرة شغّال — افتح: http://localhost:%d" % PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
