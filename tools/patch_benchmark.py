"""Bounded Python patch proposal screening. Never compile/exec/eval model source."""
import argparse
import ast
import copy
import hashlib
import json
import pathlib
import time

from coding_benchmark import MODELS, check_gpu, parse, warmup
from gpu_model_smoke import api, ready, same

CANDIDATES = ("qwen2.5-coder:14b", "qwen2.5-coder:7b")
REPORT = pathlib.Path("patch-benchmark-report.json")
MAX_SOURCE = 4000
MAX_STEPS = 2000


class Unsupported(ValueError):
    """Proposal exceeds the deliberately narrow language."""


class Rejected(Exception):
    """A candidate raises ValueError in the interpreted language."""


class Returned(Exception):
    def __init__(self, value):
        self.value = value


NODES = (
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Assign, ast.If,
    ast.For, ast.Return, ast.Raise, ast.Name, ast.Constant, ast.List, ast.Tuple,
    ast.Dict, ast.Subscript, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
    ast.Compare, ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Call, ast.Attribute,
    ast.Load, ast.Store, ast.Expr,
)
CALLS = {"isinstance", "len", "set", "ValueError"}
TYPES = {"str": str, "list": list}
METHODS = {"strip"}


class Program:
    def __init__(self, source, name, params):
        if not isinstance(source, str) or len(source) > MAX_SOURCE:
            raise Unsupported("source size")
        tree = ast.parse(source)
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise Unsupported("one function required")
        fn = tree.body[0]
        args = fn.args
        if (fn.name != name or fn.decorator_list or fn.returns or
                getattr(fn, "type_params", []) or args.posonlyargs or args.kwonlyargs
                or args.vararg or args.kwarg or args.defaults or args.kw_defaults or
                [a.arg for a in args.args] != list(params) or
                any(a.annotation for a in args.args)):
            raise Unsupported("signature")
        nodes = list(ast.walk(tree))
        if len(nodes) > 240 or any(not isinstance(n, NODES) for n in nodes):
            raise Unsupported("syntax")
        for n in nodes:
            if isinstance(n, ast.FunctionDef) and n is not fn:
                raise Unsupported("nested function")
            if isinstance(n, ast.Name) and (n.id.startswith("_") or len(n.id) > 40):
                raise Unsupported("name")
            if isinstance(n, ast.Constant) and (type(n.value) not in (str, int, bool, type(None))
                    or (type(n.value) is str and len(n.value) > 200)
                    or (type(n.value) is int and abs(n.value) > 10000)):
                raise Unsupported("constant")
            if isinstance(n, ast.Attribute) and n.attr not in METHODS:
                raise Unsupported("attribute")
            if isinstance(n, ast.Call):
                if n.keywords or not ((isinstance(n.func, ast.Name) and n.func.id in CALLS)
                        or (isinstance(n.func, ast.Attribute) and n.func.attr in METHODS)):
                    raise Unsupported("call")
            if isinstance(n, ast.Raise) and (n.cause is not None or
                    not isinstance(n.exc, ast.Call) or not isinstance(n.exc.func, ast.Name)
                    or n.exc.func.id != "ValueError"):
                raise Unsupported("raise")
        self.body = fn.body
        self.params = params

    def run(self, args):
        self.env = dict(zip(self.params, copy.deepcopy(args)))
        self.steps = MAX_STEPS
        try:
            self.block(self.body)
        except Returned as result:
            return {"result": result.value}
        except Rejected:
            return {"error": "ValueError"}
        return {"result": None}

    def tick(self):
        self.steps -= 1
        if self.steps < 0:
            raise Unsupported("step budget")

    def expr(self, n):
        self.tick()
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in self.env:
                return self.env[n.id]
            raise Unsupported("unknown name")
        if isinstance(n, (ast.List, ast.Tuple)):
            values = [self.expr(x) for x in n.elts]
            return values if isinstance(n, ast.List) else tuple(values)
        if isinstance(n, ast.Dict):
            return {self.expr(k): self.expr(v) for k, v in zip(n.keys, n.values)}
        if isinstance(n, ast.Subscript):
            obj, index = self.expr(n.value), self.expr(n.slice)
            if type(obj) not in (list, tuple, dict, str):
                raise Unsupported("subscript")
            return obj[index]
        if isinstance(n, ast.UnaryOp):
            return not self.expr(n.operand)
        if isinstance(n, ast.BoolOp):
            value = None
            for v in n.values:
                value = self.expr(v)
                if isinstance(n.op, ast.And) and not value:
                    return value
                if isinstance(n.op, ast.Or) and value:
                    return value
            return value
        if isinstance(n, ast.Compare):
            left = self.expr(n.left)
            for op, term in zip(n.ops, n.comparators):
                right = self.expr(term)
                if isinstance(op, ast.Eq):
                    ok = left == right
                elif isinstance(op, ast.NotEq):
                    ok = left != right
                elif isinstance(op, ast.In):
                    ok = left in right
                else:
                    ok = left not in right
                if not ok:
                    return False
                left = right
            return True
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                obj = self.expr(f.value)
                if f.attr == "strip" and type(obj) is str and not n.args:
                    return obj.strip()
                raise Unsupported("method")
            if f.id == "isinstance" and len(n.args) == 2:
                kind = n.args[1]
                if not isinstance(kind, ast.Name) or kind.id not in TYPES:
                    raise Unsupported("type")
                return isinstance(self.expr(n.args[0]), TYPES[kind.id])
            vals = [self.expr(x) for x in n.args]
            if f.id == "len" and len(vals) == 1 and type(vals[0]) in (list, tuple, dict, str, set):
                return len(vals[0])
            if f.id == "set" and len(vals) == 1 and type(vals[0]) in (list, tuple, str):
                return set(vals[0])
            if f.id == "ValueError" and len(vals) <= 1:
                raise Rejected()
            raise Unsupported("function")
        raise Unsupported("expression")

    def assign(self, target, value):
        self.tick()
        if isinstance(target, ast.Name):
            self.env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            if type(value) not in (tuple, list) or len(target.elts) != len(value):
                raise Unsupported("unpack")
            for t, v in zip(target.elts, value):
                self.assign(t, v)
        elif isinstance(target, ast.Subscript):
            obj, key = self.expr(target.value), self.expr(target.slice)
            if type(obj) is not dict or type(key) is not str or len(obj) >= 64 and key not in obj:
                raise Unsupported("assignment target")
            # No container aliases/cycles introduced by assignment.
            if type(value) not in (str, int, bool, type(None)):
                raise Unsupported("assignment value")
            obj[key] = value
        else:
            raise Unsupported("assignment")

    def block(self, statements):
        for n in statements:
            self.tick()
            if isinstance(n, ast.Assign):
                value = self.expr(n.value)
                for target in n.targets:
                    self.assign(target, value)
            elif isinstance(n, ast.If):
                self.block(n.body if self.expr(n.test) else n.orelse)
            elif isinstance(n, ast.For):
                seq = self.expr(n.iter)
                if type(seq) not in (list, tuple) or len(seq) > 64 or n.orelse:
                    raise Unsupported("loop")
                for value in seq:
                    self.tick()
                    self.assign(n.target, value)
                    self.block(n.body)
            elif isinstance(n, ast.Return):
                raise Returned(self.expr(n.value) if n.value else None)
            elif isinstance(n, ast.Raise):
                self.expr(n.exc)
                raise Unsupported("raise")
            else:
                raise Unsupported("statement")


ERR = {"error": "ValueError"}
def ok(v):
    return {"result": v}


# Synthetic regressions derived from the evaluator's public helper contracts.
TASKS = (
    ("duplicate_keys", "unique_object", ("pairs",),
     "Reject a repeated key with ValueError even when its value is identical. Preserve values for unique keys.",
     "def unique_object(pairs):\n    result = {}\n    for key, value in pairs:\n        result[key] = value\n    return result",
     "def unique_object(pairs):\n    result = {}\n    for key, value in pairs:\n        if key in result:\n            raise ValueError('duplicate')\n        result[key] = value\n    return result",
     [( [ [] ], ok({})), ([[["a", 0], ["b", False]]], ok({"a": 0, "b": False})),
      ([[["x", None], ["x", None]]], ERR), ([[["a", 1], ["b", 2], ["a", 3]]], ERR),
      ([[["ñ", "value"], ["", True]]], ok({"ñ": "value", "": True}))]),
    ("nonempty_text", "text_value", ("value", "field"),
     "Return the original string unchanged if it contains at least one non-whitespace character. Otherwise raise ValueError, including for non-strings.",
     "def text_value(value, field):\n    if not isinstance(value, str):\n        raise ValueError(field)\n    return value",
     "def text_value(value, field):\n    if not isinstance(value, str) or not value.strip():\n        raise ValueError(field)\n    return value",
     [([" hello ", "x"], ok(" hello ")), (["", "x"], ERR), ([" \t\n", "x"], ERR),
      ([False, "x"], ERR), ([None, "x"], ERR), (["é", "x"], ok("é"))]),
    ("unique_string_list", "strings_value", ("value", "field"),
     "Require a list of nonempty, non-whitespace strings without duplicates. Return the original list, including its order and exact strings. Reject invalid inputs with ValueError. Empty list is valid. Compare exact strings, not stripped strings.",
     "def strings_value(value, field):\n    if not isinstance(value, list):\n        raise ValueError(field)\n    return value",
     "def strings_value(value, field):\n    if not isinstance(value, list):\n        raise ValueError(field)\n    for item in value:\n        if not isinstance(item, str) or not item.strip():\n            raise ValueError(field)\n    if len(set(value)) != len(value):\n        raise ValueError(field)\n    return value",
     [([[], "x"], ok([])), ([["b", "a"], "x"], ok(["b", "a"])),
      ([["a", "a"], "x"], ERR), ([[" "], "x"], ERR), ([[0], "x"], ERR),
      ([["a", " a "], "x"], ok(["a", " a "])), (["a", "x"], ERR),
      ([["a", "b", "a"], "x"], ERR)]),
)


def assess_source(source, task):
    _, name, params, _, _, _, cases = task
    program = Program(source, name, params)
    results = []
    for args, expected in cases:
        try:
            results.append(same(program.run(args), expected))
        except (Unsupported, TypeError, KeyError, IndexError, ValueError):
            results.append(False)
    return {"passed_cases": sum(results), "total_cases": len(results),
            "passed": all(results)}


def self_test():
    for task in TASKS:
        assert assess_source(task[5], task)["passed"], task[0]
        assert not assess_source(task[4], task)["passed"], task[0]
    bad = (
        "def unique_object(pairs):\n    import os\n    return {}",
        "def unique_object(pairs):\n    return open('x')",
        "def unique_object(pairs):\n    return pairs.__class__",
        "def unique_object(pairs):\n    while True:\n        return {}",
        "def unique_object(pairs):\n    return eval('1')",
        "def unique_object(pairs):\n    return {}\nprint('x')",
    )
    for source in bad:
        try:
            Program(source, "unique_object", ("pairs",))
        except (Unsupported, SyntaxError):
            continue
        raise AssertionError("unsafe syntax accepted")
    print("Patch benchmark self-test passed: 3 reference fixes, 3 regressions, 6 forbidden proposals")


def run(model):
    start = time.monotonic()
    report = {"schema": 1, "model": model, "stage": "metadata",
              "tasks": [], "qualified": False}
    try:
        ready()
        entry = next(m for m in api("/api/tags")["models"] if m["name"] == model)
        digest = entry["digest"].removeprefix("sha256:")
        if digest != MODELS[model]:
            raise ValueError("unexpected digest")
        report["digest"] = digest
        report["stage"] = "warmup"
        report["warmup"] = warmup(model)
        report["stage"] = "tasks"
        for task in TASKS:
            ident, name, params, contract, broken, _, _ = task
            item = {"id": ident, "status": "incomplete", "passed": False}
            report["tasks"].append(item)
            t0 = time.monotonic()
            try:
                prompt = (
                    "Fix the Python function below. Return exactly a JSON object "
                    "with key source containing the complete corrected function as a string. "
                    "Keep the name and parameters. No imports, annotations, decorators, "
                    "comprehensions, while, try, f-strings or other functions. "
                    "Allowed: assignment, if, for, return, raise ValueError, "
                    "literals, indexing, comparisons, and/or/not, isinstance(x,str/list), "
                    "len, set, and string.strip(). Use plain string error messages. "
                    "Contract: " + contract + "\nBroken function:\n" + broken
                )
                response = api("/api/generate", {"model": model, "prompt": prompt,
                    "stream": False, "format": "json", "keep_alive": "5m",
                    "options": {"temperature": 0, "seed": 42, "num_ctx": 4096,
                                "num_predict": 768}}, timeout=150)
                if response.get("done") is not True or response.get("done_reason") == "length":
                    raise ValueError("incomplete generation")
                item["gpu_bytes"] = check_gpu(model)
                item["generation"] = {k: response[k] for k in
                    ("eval_count", "eval_duration", "total_duration", "load_duration")
                    if type(response.get(k)) is int}
                try:
                    value = parse(response["response"])
                    if not isinstance(value, dict) or set(value) != {"source"}:
                        raise Unsupported("response shape")
                    source = value["source"]
                    if not isinstance(source, str) or len(source) > MAX_SOURCE:
                        raise Unsupported("source size")
                    item["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
                    # Store only bounded proposal text for human review, never execute it.
                    item["proposal"] = source
                    item.update(assess_source(source, task))
                    item["status"] = "correct" if item["passed"] else "incorrect"
                except (ValueError, SyntaxError, KeyError, TypeError) as exc:
                    item["status"] = "rejected"
                    item["error_type"] = type(exc).__name__
            except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
                item["error_type"] = type(exc).__name__
            finally:
                item["wall_seconds"] = round(time.monotonic() - t0, 3)
                REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report["stage"] = "completed"
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
        report["error_type"] = type(exc).__name__
    finally:
        report["passed_tasks"] = sum(t["passed"] for t in report["tasks"])
        report["complete"] = len(report["tasks"]) == len(TASKS) and all(
            t["status"] != "incomplete" and t.get("gpu_bytes", 0) > 0 for t in report["tasks"])
        report["qualified"] = report["complete"] and report["passed_tasks"] == len(TASKS)
        report["wall_seconds"] = round(time.monotonic() - start, 3)
        REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        # Do not echo model text into CI logs.
        print(json.dumps({**report, "tasks": [
            {k: v for k, v in t.items() if k != "proposal"} for t in report["tasks"]
        ]}, sort_keys=True))
    return 0 if report["qualified"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--model", choices=CANDIDATES)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        raise SystemExit(run(args.model))
