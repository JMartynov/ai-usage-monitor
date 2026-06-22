import timeit

def with_tuple():
    headers = {
        "Host": "localhost:8000",
        "User-Agent": "curl/7.68.0",
        "Accept": "*/*",
        "Content-Length": "100",
        "Connection": "keep-alive",
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "X-Custom-Header": "custom-value"
    }
    return {
        k: v for k, v in headers.items()
        if k.lower() not in (
            "host",
            "content-length",
            "connection",
            "accept-encoding"
        )
    }

def with_set():
    headers = {
        "Host": "localhost:8000",
        "User-Agent": "curl/7.68.0",
        "Accept": "*/*",
        "Content-Length": "100",
        "Connection": "keep-alive",
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "X-Custom-Header": "custom-value"
    }
    return {
        k: v for k, v in headers.items()
        if k.lower() not in {
            "host",
            "content-length",
            "connection",
            "accept-encoding"
        }
    }

def with_set_global():
    headers = {
        "Host": "localhost:8000",
        "User-Agent": "curl/7.68.0",
        "Accept": "*/*",
        "Content-Length": "100",
        "Connection": "keep-alive",
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "X-Custom-Header": "custom-value"
    }
    EXCLUDED_HEADERS = {"host", "content-length", "connection", "accept-encoding"}
    return {
        k: v for k, v in headers.items()
        if k.lower() not in EXCLUDED_HEADERS
    }

if __name__ == "__main__":
    n = 1000000
    time_tuple = timeit.timeit("with_tuple()", globals=globals(), number=n)
    time_set = timeit.timeit("with_set()", globals=globals(), number=n)
    time_set_global = timeit.timeit("with_set_global()", globals=globals(), number=n)
    print(f"Tuple: {time_tuple:.4f}s")
    print(f"Set: {time_set:.4f}s")
    print(f"Set (global): {time_set_global:.4f}s")
