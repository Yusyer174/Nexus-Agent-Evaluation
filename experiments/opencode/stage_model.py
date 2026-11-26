"""Prepare the exact, previously measured Ollama model for an offline namespace."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request

from coding_benchmark import MODELS

REGISTRY = "https://registry.ollama.ai/v2/library/qwen2.5-coder"
EXPECTED = MODELS["qwen2.5-coder:14b"]


def stage(models):
    with urllib.request.urlopen(REGISTRY + "/manifests/14b", timeout=20) as response:
        manifest = response.read(65537)
    if hashlib.sha256(manifest).hexdigest() != EXPECTED:
        raise ValueError("registry tag changed")
    data = json.loads(manifest)
    blobs = [data["config"], *data["layers"]]
    size = sum(item["size"] for item in blobs)
    if shutil.disk_usage(models).free < size + 2 * 1024**3:
        raise OSError("insufficient space for the pinned layers")
    dest = models / "blobs"
    dest.mkdir()
    for item in blobs:
        digest = item["digest"]
        if not digest.startswith("sha256:") or len(digest) != 71:
            raise ValueError("invalid layer descriptor")
        h = hashlib.sha256()
        count = 0
        with urllib.request.urlopen(REGISTRY + "/blobs/" + digest, timeout=45) as response:
            with (dest / digest.replace(":", "-")).open("xb") as output:
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > item["size"]:
                        raise ValueError("oversized layer")
                    output.write(chunk)
                    h.update(chunk)
        if count != item["size"] or h.hexdigest() != digest[7:]:
            raise ValueError("layer verification failed")
    entry = models / "manifests/registry.ollama.ai/library/qwen2.5-coder/14b"
    entry.parent.mkdir(parents=True)
    entry.write_bytes(manifest)


if __name__ == "__main__":
    stage(Path(sys.argv[1]))
