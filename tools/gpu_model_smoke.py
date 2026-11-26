"""Bounded GPU model baseline. Model outputs are data, never executable code."""
import argparse
import inspect
import json
import pathlib
import time
import urllib.request

from evaluator import _unique_object

MODEL = "qwen2.5-coder:7b"
EXPECTED_DIGEST = "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364"
VERSION = "0.40.18"
URL = "http://127.0.0.1:11434"
REPORT = pathlib.Path("model-smoke-report.json")
MAX_RESPONSE = 1024 * 1024


def api(path, data=None, timeout=10):
    request = urllib.request.Request(
        URL + path, data=None if data is None else json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("API response exceeds limit")
    return json.loads(raw, object_pairs_hook=_unique_object)


def ready():
    for _ in range(45):
        try:
            if api("/api/version")["version"] == VERSION:
                return
            raise ValueError("Unexpected Ollama version")
        except OSError:
            time.sleep(1)
    raise RuntimeError("Ollama server did not become ready")


def same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(
        b, sort_keys=True, allow_nan=False
    )


def assess(cases):
    if not isinstance(cases, list) or not 3 <= len(cases) <= 8:
        raise ValueError("Expected three to eight cases")
    coverage = set()
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"pairs", "expected"}:
            raise ValueError("Invalid case fields")
        pairs, expected = case["pairs"], case["expected"]
        if not isinstance(pairs, list) or len(pairs) > 8:
            raise ValueError("Invalid pairs")
        for pair in pairs:
            if (not isinstance(pair, list) or len(pair) != 2
                    or type(pair[0]) is not str or not 1 <= len(pair[0]) <= 40
                    or type(pair[1]) not in (str, int, bool, type(None))
                    or (type(pair[1]) is str and len(pair[1]) > 80)
                    or (type(pair[1]) is int and abs(pair[1]) > 1000000)):
                raise ValueError("Invalid pair")
        identity = json.dumps(pairs, ensure_ascii=True, sort_keys=True)
        if identity in seen:
            raise ValueError("Duplicate test case")
        seen.add(identity)
        keys = [p[0] for p in pairs]
        duplicates = len(set(keys)) != len(keys)
        # Independent oracle, not the implementation under test.
        oracle = {"error": "ValueError"} if duplicates else {"result": dict(pairs)}
        if not same(expected, oracle):
            raise ValueError("Incorrect expected result")
        try:
            actual = {"result": _unique_object(pairs)}
        except ValueError:
            actual = {"error": "ValueError"}
        if not same(actual, oracle):
            raise ValueError("Implementation disagrees with oracle")
        if not pairs:
            coverage.add("empty")
        elif duplicates:
            coverage.add("duplicate")
        elif len(keys) >= 2:
            coverage.add("distinct")
    required = {"empty", "duplicate", "distinct"}
    return {"cases": len(cases), "coverage": sorted(coverage),
            "passed": coverage == required}


def self_test():
    good = [
        {"pairs": [], "expected": {"result": {}}},
        {"pairs": [["a", 1], ["b", False]], "expected": {"result": {"a": 1, "b": False}}},
        {"pairs": [["a", 1], ["a", 2]], "expected": {"error": "ValueError"}},
    ]
    assert assess(good)["passed"]
    wrong = good[:2] + [{"pairs": [["a", 1], ["a", 2]], "expected": {"result": {"a": 2}}}]
    malformed = good[:2] + [{"pairs": [["a", {}]], "expected": {"result": {"a": {}}}}]
    for invalid in (wrong, malformed, good[:2], good + [good[0]]):
        try:
            assess(invalid)
        except ValueError:
            continue
        raise AssertionError("Invalid case was accepted")
    incomplete = good[:2] + [{"pairs": [["x", 3]], "expected": {"result": {"x": 3}}}]
    assert not assess(incomplete)["passed"]
    print("Harness self-test passed (six scenarios)")


def run():
    report = {"model": MODEL, "passed": False, "stage": "metadata"}
    try:
        ready()
        tags = api("/api/tags")["models"]
        entry = next(m for m in tags if m["name"] == MODEL)
        digest = entry["digest"].removeprefix("sha256:")
        if digest != EXPECTED_DIGEST:
            raise ValueError("Unexpected model digest")
        report.update({"digest": digest, "ollama": VERSION, "stage": "generation"})
        prompt = (
            "Design three to eight distinct test cases for this Python function. "
            "Cover empty input, distinct keys with preserved values, and duplicate keys. "
            "Return ONLY a JSON object with key cases, containing objects with keys "
            "pairs and expected. pairs is a list of [string, scalar] lists. "
            "Scalars may be strings, integers, booleans or null. "
            "expected is either {\"result\": {key: value}} or {\"error\": \"ValueError\"}. "
            "Do not output Python code. Function:\n" + inspect.getsource(_unique_object)
        )
        output = api("/api/generate", {
            "model": MODEL, "prompt": prompt, "stream": False, "format": "json",
            "keep_alive": "5m", "options": {"temperature": 0, "seed": 42,
                                            "num_ctx": 4096, "num_predict": 1024},
        }, timeout=300)
        if output.get("done") is not True:
            raise ValueError("Incomplete model response")
        report["generation"] = {k: output[k] for k in (
            "total_duration", "load_duration", "prompt_eval_count",
            "eval_count", "eval_duration") if type(output.get(k)) is int}
        report["stage"] = "gpu_verification"
        running = next(m for m in api("/api/ps")["models"] if m["name"] == MODEL)
        gpu_bytes = running.get("size_vram", 0)
        report["gpu_bytes"] = gpu_bytes
        if type(gpu_bytes) is not int or gpu_bytes <= 0:
            raise ValueError("No model bytes resident in GPU memory")
        report["stage"] = "assessment"
        parsed = json.loads(output["response"], object_pairs_hook=_unique_object)
        if not isinstance(parsed, dict) or set(parsed) != {"cases"}:
            raise ValueError("Invalid response fields")
        result = assess(parsed["cases"])
        report.update(result)
        report["passed"] = result["passed"]
        report["stage"] = "completed"
    except Exception as exc:
        report["error_type"] = type(exc).__name__
    finally:
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--ready", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.ready:
        ready()
    else:
        raise SystemExit(run())
