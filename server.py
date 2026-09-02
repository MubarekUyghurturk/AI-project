import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

PORT = int(os.environ.get("PORT", 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "contacts.json")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

MIME = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
}

CONTACT_ID_RE = re.compile(r"^/api/contacts/([^/]+)$")
NAME_ALLOWED_EXTRA = " -'"


def is_valid_name(value):
    if not value:
        return False
    return all(ch.isalpha() or ch in NAME_ALLOWED_EXTRA for ch in value)


def read_contacts():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        return json.loads(raw) if raw else []


def write_contacts(contacts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(PUBLIC_DIR, path.lstrip("/")))
        if not file_path.startswith(PUBLIC_DIR):
            self.send_response(403)
            self.end_headers()
            return
        if not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        ext = os.path.splitext(file_path)[1]
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/contacts":
            return self._send_json(200, read_contacts())
        self._serve_static()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/contacts":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return self._send_json(400, {"error": "Invalid JSON"})

        first_name = (parsed.get("firstName") or "").strip()
        last_name = (parsed.get("lastName") or "").strip()
        if not first_name or not last_name:
            return self._send_json(400, {"error": "First and last name are required"})
        if not is_valid_name(first_name) or not is_valid_name(last_name):
            return self._send_json(
                400,
                {"error": "Names may only contain letters, spaces, hyphens, and apostrophes"},
            )

        contacts = read_contacts()
        contact = {
            "id": str(int(time.time() * 1000)),
            "firstName": first_name,
            "lastName": last_name,
        }
        contacts.append(contact)
        write_contacts(contacts)
        self._send_json(201, contact)

    def do_DELETE(self):
        path = urlparse(self.path).path
        match = CONTACT_ID_RE.match(path)
        if not match:
            self.send_response(404)
            self.end_headers()
            return
        contact_id = match.group(1)
        contacts = [c for c in read_contacts() if c["id"] != contact_id]
        write_contacts(contacts)
        self._send_json(200, {"ok": True})

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Contact list app running at http://localhost:{PORT}")
    server.serve_forever()
