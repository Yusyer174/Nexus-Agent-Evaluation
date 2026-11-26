"""Read-only NVIDIA CUDA driver check without downloading or executing a model."""
import ctypes
import json


def main():
    report = {"passed": False, "stage": "load_driver"}
    try:
        lib = ctypes.CDLL("libcuda.so.1")
        report["stage"] = "initialize"
        lib.cuInit.argtypes = [ctypes.c_uint]
        lib.cuInit.restype = ctypes.c_int
        result = lib.cuInit(0)
        report["cuInit"] = result
        if result != 0:
            return report
        report["stage"] = "device_count"
        count = ctypes.c_int()
        lib.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
        lib.cuDeviceGetCount.restype = ctypes.c_int
        result = lib.cuDeviceGetCount(ctypes.byref(count))
        report.update({"cuDeviceGetCount": result, "device_count": count.value})
        report["passed"] = result == 0 and count.value > 0
    except (OSError, AttributeError) as exc:
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
    return report


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)
