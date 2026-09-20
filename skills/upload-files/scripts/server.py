#!/usr/bin/env python3
"""Temporary upload-only server; Python standard library, no multipart parser."""

import argparse
import hmac
import json
import os
from pathlib import Path
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

MAX_BYTES = 1024 ** 3
PAGE = b"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload files</title>
<style>
body { font: 16px system-ui, sans-serif; background: #f4f6f8; color: #17283b;
       margin: 0; padding: 48px 20px; }
main { max-width: 640px; margin: auto; }
h1 { font-size: 32px; margin-bottom: 8px; }
p { line-height: 1.6; }
#drop { background: white; border: 2px dashed #728399; border-radius: 12px;
        padding: 40px 24px; margin: 28px 0; text-align: center; }
#drop.over { background: #e3efff; border-color: #245aa5; }
input { max-width: 100%; margin-top: 16px; }
li { margin: 12px 0; overflow-wrap: anywhere; }
.ok { color: #166334; } .error { color: #a12222; }
</style>
<main><h1>Upload files</h1>
<p>Send files to .agentic/uploads in the working directory, excluded from Git.</p>
<section id="drop" aria-label="File drop area"><strong>Drag files here</strong><br>
<label for="files">or choose files from your computer</label><br>
<input id="files" type="file" multiple></section>
<p>Up to 1 GiB per file. Existing filenames are never overwritten.</p>
<p id="notice" role="status"></p><ul id="results" aria-live="polite"></ul></main>
<script>
const token = new URLSearchParams(location.hash.slice(1)).get('token') || '';
const drop = document.querySelector('#drop');
const input = document.querySelector('#files');
if (!token) {
  document.querySelector('#notice').textContent = 'Open the session link supplied by your agent to enable uploads.';
  input.disabled = true;
}
async function upload(files) {
  if (!token) return;
  for (const file of files) {
    const row = document.createElement('li');
    document.querySelector('#results').append(row);
    row.textContent = `${file.name} - Uploading...`;
    try {
      if (file.size > 1073741824) throw new Error('File exceeds 1 GiB');
      const response = await fetch('/upload?name=' + encodeURIComponent(file.name), {
        method: 'POST', headers: {'Authorization': 'Bearer ' + token}, body: file
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      row.textContent = `${file.name} - Uploaded (${result.bytes} bytes)`;
      row.className = 'ok';
    } catch (error) {
      row.textContent = `${file.name} - ${error.message}`;
      row.className = 'error';
    }
  }
}
input.addEventListener('change', () => { upload([...input.files]); input.value = ''; });
document.addEventListener('dragover', event => event.preventDefault());
document.addEventListener('drop', event => event.preventDefault());
drop.addEventListener('dragover', () => drop.classList.add('over'));
drop.addEventListener('dragleave', () => drop.classList.remove('over'));
drop.addEventListener('drop', event => {
  drop.classList.remove('over'); upload([...event.dataTransfer.files]);
});
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(60)

    def log_message(self, *_):
        pass  # Do not log credentials or user-supplied names.

    def respond(self, status, data, content_type="application/json"):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.respond(200, PAGE, "text/html; charset=utf-8")
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if not hmac.compare_digest(
            self.headers.get("Authorization", "").encode(),
            ("Bearer " + self.server.token).encode(),
        ):
            self.respond(403, {"error": "Invalid session token"})
            return
        url = urlsplit(self.path)
        if url.path != "/upload":
            self.respond(404, {"error": "Not found"})
            return
        name = parse_qs(url.query).get("name", [""])[0]
        if not name or name in (".", "..") or any(c in name for c in "/\\\x00"):
            self.respond(400, {"error": "Invalid filename"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = -1
        if self.headers.get("Transfer-Encoding") or not 0 <= length <= MAX_BYTES:
            self.respond(413, {"error": "A Content-Length of 0 to 1 GiB is required"})
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.server.staging, delete=False) as output:
                temporary = Path(output.name)
                remaining = length
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise OSError("Incomplete upload")
                    output.write(chunk)
                    remaining -= len(chunk)
            # Atomic publication, with no overwrite even for concurrent requests.
            os.link(temporary, self.server.uploads / name)
        except FileExistsError:
            self.respond(409, {"error": "Filename already exists; rename and retry"})
        except OSError:
            self.respond(500, {"error": "Upload failed; check disk space and filename, then retry"})
        else:
            self.respond(201, {"name": name, "bytes": length})
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path.cwd() / ".agentic",
                        help="Storage root (default: .agentic in the current directory)")
    args = parser.parse_args()
    os.umask(0o077)
    directory = args.directory.resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix="upload-files-", dir=directory))
    with ThreadingHTTPServer(("0.0.0.0", 0), Handler) as server:
        server.uploads = directory / "uploads"
        server.staging = session / "incomplete"
        server.uploads.mkdir(exist_ok=True)
        server.staging.mkdir(exist_ok=True)
        server.token = secrets.token_urlsafe(32)
        state = {"port": server.server_port, "token": server.token, "directory": str(server.uploads)}
        pending = session / "session.json.tmp"
        pending.write_text(json.dumps(state))
        pending.replace(session / "session.json")
        print(f"Listening on 0.0.0.0:{server.server_port}; session: {session}/session.json", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
