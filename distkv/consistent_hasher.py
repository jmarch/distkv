import hashlib
import threading


class ConsistentHasher:
    def __init__(self, replicas=3) -> None:
        self.replicas = replicas
        self.ring = dict()
        self.sorted_keys = []
        self.lock = threading.Lock()

    def hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode('utf-8')).hexdigest()[0:8], 16)

    def ring_ranges(self):
        return list(zip(list(zip([0] + self.sorted_keys, self.sorted_keys + [int('1' + '0'*8, 16)])), [self.ring[i] for i in [self.sorted_keys[-1]] + self.sorted_keys]))

    def add_node(self, node: str) -> None:
        with self.lock:
            for i in range(self.replicas):
                self.ring[self.hash(f"{node}:{i}")] = node
            self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node: str) -> None:
        with self.lock:
            for i in range(self.replicas):
                del self.ring[self.hash(f"{node}:{i}")]
            self.sorted_keys = sorted(self.ring.keys())

    def update_nodes(self, zk_nodes: list[str]) -> None:
        zk_nodes = set(zk_nodes)
        current_nodes = set(self.ring.values())
        for node in zk_nodes - current_nodes:
            self.add_node(node)
        for node in current_nodes - zk_nodes:
            self.remove_node(node)

    def get_node(self, key: str) -> str:
        with self.lock:
            if not self.ring:
                return None
            hash_key = self.hash(key)
            idx = self._find_index(hash_key)
        return self.ring[self.sorted_keys[idx]]

    def _find_index(self, hash_key: int) -> int:
        low, high = 0, len(self.sorted_keys) - 1
        if hash_key > self.sorted_keys[high] or hash_key < self.sorted_keys[0]:
            return 0
        while low <= high:
            mid = (low + high) // 2
            if self.sorted_keys[mid] == hash_key:
                return mid
            elif self.sorted_keys[mid] < hash_key:
                low = mid + 1
            else:
                high = mid - 1
        return low

