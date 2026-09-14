"""Exercise npm latest selection and updates against an in-memory local registry."""

import base64
import hashlib
import io
import json
import os
import subprocess
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote


def test_npm_latest_ignores_other_tags_and_tracks_stable_updates(tmp_path):
    name = "@knowledge-bus/pi"
    archives = {}
    for version in ("0.5.0", "0.6.0"):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as tar:
            data = json.dumps(
                {"name": name, "version": version, "pi": {"skills": ["./skills"]}}
            ).encode()
            member = tarfile.TarInfo("package/package.json")
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
        archives[version] = stream.getvalue()
    latest = ["0.5.0"]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = unquote(self.path)
            if route == "/" + name:
                versions = {
                    version: {
                        "name": name,
                        "version": version,
                        "dist": {
                            "tarball": f"http://127.0.0.1:{self.server.server_port}/{version}.tgz",
                            "integrity": "sha512-"
                            + base64.b64encode(hashlib.sha512(data).digest()).decode(),
                        },
                    }
                    for version, data in archives.items()
                }
                payload = json.dumps(
                    {
                        "name": name,
                        "dist-tags": {"latest": latest[0], "candidate": "0.6.0"},
                        "versions": versions,
                    }
                ).encode()
            elif route.endswith(".tgz") and route[1:-4] in archives:
                payload = archives[route[1:-4]]
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    (tmp_path / "package.json").write_text('{"private":true}')
    config = tmp_path / "empty.npmrc"
    config.write_text("")
    env = {
        **os.environ,
        "npm_config_cache": str(tmp_path / "cache"),
        "npm_config_userconfig": str(config),
    }
    try:
        for expected in ("0.5.0", "0.5.0", "0.6.0"):
            latest[0] = expected
            result = subprocess.run(
                [
                    "npm",
                    "install",
                    name + "@latest",
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                    "--prefer-online",
                    "--registry",
                    f"http://127.0.0.1:{server.server_port}",
                ],
                cwd=tmp_path,
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            package = json.loads(
                (tmp_path / "node_modules" / name / "package.json").read_text()
            )
            assert package["version"] == expected
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
