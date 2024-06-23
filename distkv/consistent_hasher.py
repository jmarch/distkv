import hashlib
import threading


class ConsistentHasher:
    def __init__(self, replicas=3):
        self.replicas = replicas
        self.ring = dict()
        self.sorted_keys = []
        self.lock = threading.Lock()

    def hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        with self.lock:
            for i in range(self.replicas):
                self.ring[self.hash(f"{node}:{i}")] = node
            self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node):
        with self.lock:
            for i in range(self.replicas):
                del self.ring[self.hash(f"{node}:{i}")]
            self.sorted_keys = sorted(self.ring.keys())

    def update_nodes(self, zk_nodes):
        zk_nodes = set(zk_nodes)
        current_nodes = set(self.ring.values())
        nodes_to_add = zk_nodes - current_nodes
        for node in nodes_to_add:
            self.add_node(node)
        nodes_to_remove = current_nodes - zk_nodes
        for node in nodes_to_remove:
            self.remove_node(node)

    def get_node(self, key):
        with self.lock:
            if not self.ring:
                return None
            hash_key = self.hash(key)
            idx = self._find_index(hash_key)
            return self.ring[self.sorted_keys[idx]]

    def _find_index(self, hash_key):
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

