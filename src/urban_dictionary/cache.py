import time


class Cache:
    def __init__(self, ttl=300):
        self._ttl = ttl
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["time"] > self._ttl:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key, value):
        self._store[key] = {"value": value, "time": time.monotonic()}

    def clear(self):
        self._store.clear()
