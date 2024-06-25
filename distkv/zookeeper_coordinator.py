from .consistent_hasher import ConsistentHasher
from kazoo.client import KazooClient
from kazoo.recipe.watchers import ChildrenWatch


class ZookeeperCoordinator:
    def __init__(self, hosts: str, cluster_path: str, hasher: ConsistentHasher) -> None:
        self.hosts = hosts
        self.cluster_path = cluster_path
        self.nodes_path = f"{cluster_path}/nodes"
        self.hasher = hasher

        self.zk = KazooClient(hosts=self.hosts)
        self.zk.start()

        for p in [self.cluster_path, self.nodes_path]:
            if not self.zk.exists(p):
                self.zk.ensure_path(p)

        def watch_nodes(children):
            self.hasher.update_nodes(children)
        ChildrenWatch(self.zk, self.nodes_path, watch_nodes)

    def register_node(self, node: str) -> None:
        node_path = f"{self.nodes_path}/{node}"
        if not self.zk.exists(node_path):
            self.zk.create(node_path, ephemeral=True)
        self.hasher.add_node(node)

    def unregister_node(self, node: str) -> None:
        nodes_path = f"{self.nodes_path}/{node}"
        if self.zk.exists(nodes_path):
            self.zk.delete(nodes_path)
        self.hasher.remove_node(node)

    def shutdown(self) -> None:
        self.zk.stop()
        self.zk.close()

