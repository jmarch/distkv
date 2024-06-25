from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.cache = OrderedDict()
        self.capacity = capacity

    def lru(self) -> str:
        return ','.join(self.cache)

    def get(self, key: str) -> str:
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key not in self.cache and len(self.cache) == self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value
        self.cache.move_to_end(key)

