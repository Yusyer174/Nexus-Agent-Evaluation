"""Drive the real pinned OpenCode CLI using scripted responses. No model inference."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

from pilot import MODEL

CONFIG = Path(__file__).with_name("opencode.json")


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, value):
        payload = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path != "/api/tags":
            return self.send_error(404)
        self.reply({"models": [{"name": MODEL, "model": MODEL, "digest": "a" * 64,
                                "size": 42, "modified_at": "2026-01-01T00:00:00Z",
                                "details": {"format": "gguf", "family": "qwen2", "families": ["qwen2"],
                                            "parameter_size": "14B", "quantization_level": "Q4_K_M",
                                            "parent_model": ""}}]})

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/show":
            return self.reply({"capabilities": ["completion", "tools"],
                               "model_info": {"general.architecture": "qwen2", "qwen2.context_length": 65536},
                               "details": {"family": "qwen2"}})
        if self.path != "/v1/chat/completions" or data.get("model") != MODEL:
            return self.send_error(404)
        offered = {t["function"]["name"] for t in data.get("tools", [])}
        if offered:
            self.server.offered.update(offered)
        previous = any(m["role"] == "tool" for m in data.get("messages", []))
        delta = {"role": "assistant", "content": "End of scripted control."}
        reason = "stop"
        if offered and not previous:
            delta = {"role": "assistant", "tool_calls": [
                {"index": 0, "id": "call_control", "type": "function",
                 "function": {"name": "read", "arguments": json.dumps({"path": self.server.target})}}]}
            reason = "tool_calls"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for part, finish in ((delta, None), ({}, reason)):
            chunk = {"id": "chatcmpl-control", "object": "chat.completion.chunk", "created": 1,
                     "model": MODEL, "choices": [{"index": 0, "delta": part, "finish_reason": finish}]}
            self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
        self.wfile.write(b"data: [DONE]\n\n")


def control(binary):
    report = {"mode": "scripted_provider_real_cli", "gpu_minutes": 0, "model_inferences": 0, "checks": {}}
    with tempfile.TemporaryDirectory() as temp, ThreadingHTTPServer(("127.0.0.1", 0), Fixture) as server:
        root = Path(temp)
        project = root / "fixture"
        project.mkdir()
        home = root / "home"
        home.mkdir()
        server.offered = set()
        config = json.loads(CONFIG.read_text())
        config["providers"]["ollama"]["settings"]["baseURL"] = f"http://127.0.0.1:{server.server_port}/v1"
        (project / "opencode.json").write_text(json.dumps(config))
        (project / "task-note.txt").write_text("PUBLIC_READ_CONTROL")
        (project / "blocked.txt").write_text("DENIED_CONTROL_CONTENT")
        (root / "outside.txt").write_text("DENIED_CONTROL_CONTENT")
        env = {"HOME": str(home), "PATH": os.defpath}
        report["cli"] = subprocess.check_output([binary, "--version"], env=env, text=True).strip()
        if report["cli"] != "opencode v2.4.2":
            raise ValueError("unexpected CLI version")
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            for path in ("task-note.txt", "blocked.txt", "../outside.txt", "opencode.json"):
                server.target = path
                cli = subprocess.run([binary, "run", "--standalone", "--model", "ollama/" + MODEL,
                                      "--format", "json", "Exercise the scripted read control."],
                                     cwd=project, env=env, capture_output=True, text=True, timeout=30)
                calls = [e["part"] for e in map(json.loads, cli.stdout.splitlines()) if e["type"] == "tool_use"]
                valid = len(calls) == 1 and calls[0]["tool"] == "read" and calls[0]["state"]["input"] == {"path": path}
                state = calls[0]["state"] if valid else {}
                if path == "task-note.txt":
                    passed = state.get("status") == "completed" and "PUBLIC_READ_CONTROL" in state["output"]
                else:
                    passed = (state.get("status") == "error"
                              and any(word in state.get("error", "").lower() for word in ("denied", "policy", "reject", "permission", "blocked"))
                              and "DENIED_CONTROL_CONTENT" not in cli.stdout)
                report["checks"][path] = bool(valid and passed)
            report["checks"]["offered_only_read"] = server.offered == {"read"}
        finally:
            server.shutdown()
    report["passed"] = all(report["checks"].values())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    args = parser.parse_args()
    result = control(str(args.binary.resolve()))
    print(json.dumps(result, indent=2))
    raise SystemExit(not result["passed"])
