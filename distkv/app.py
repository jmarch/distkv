from .consistent_hasher import ConsistentHasher
from .lru_cache import LRUCache
from .zookeeper_coordinator import ZookeeperCoordinator

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
#from wsgiref.simple_server import make_server
import bjoern
import falcon
import json
import socket
import sys

REQUEST_COUNT = Counter('request_count', 'Request count')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

#POST_REQUEST_COUNT = Counter('post_request_count', 'POST request count')
#POST_REQUEST_LATENCY = Histogram('post_request_latency_seconds', 'POST request latency')

#GET_REQUEST_COUNT = Counter('get_request_count', 'GET request count')
#GET_REQUEST_LATENCY = Histogram('get_request_latency_seconds', 'GET request latency')

ZK_HOSTS = 'zoo1:2181,zoo2:2181,zoo3:2181'
#ZK_HOSTS = '127.0.0.1:2181,127.0.0.1:2182,127.0.0.1:2183'
ZK_SERVICE_BASE = '/distkv'


class MetricsResource:
    def on_get(self, req, resp):
        resp.content_type = CONTENT_TYPE_LATEST
        resp.body = generate_latest()


class KVResource:
    def __init__(self, server_str, consistent_hasher):
        self.server_str = server_str
        self.consistent_hasher = consistent_hasher
        self.cache = LRUCache(capacity=3)

    def on_get(self, req, resp, key):
        with REQUEST_LATENCY.time():
            REQUEST_COUNT.inc()
            dest_server = self.consistent_hasher.get_node(key)
            if dest_server != self.server_str:
                raise falcon.HTTPPermanentRedirect(f"http://{dest_server}{req.path}")
            value = self.cache.get(key)
            resp.content_type = falcon.MEDIA_JSON
            resp.text = json.dumps({'key': key, 'value': value, 'type': req.method, 'LRU': self.cache.lru(), 'server': self.server_str}, indent=4, sort_keys=True)
            resp.status = falcon.HTTP_200

    def on_post(self, req, resp, key):
        with REQUEST_LATENCY.time():
            REQUEST_COUNT.inc()
            dest_server = self.consistent_hasher.get_node(key)
            if dest_server != self.server_str:
                raise falcon.HTTPPermanentRedirect(f"http://{dest_server}{req.path}")
            value = req.get_param('value')
            if value is None:
                raise falcon.HTTPBadRequest(
                    title='Missing value',
                    description='A value must be submitted on POST.',
                )
            self.cache.put(key, value)
            resp.content_type = falcon.MEDIA_JSON
            resp.text = json.dumps({'key': key, 'value': value, 'type': req.method, 'LRU': self.cache.lru(), 'server': self.server_str}, indent=4, sort_keys=True)
            resp.status = falcon.HTTP_200


def main():
    if len(sys.argv) < 3:
        print("Usage:  distkv <cluster_name> <port>")
        return 1

    # Detect the hostname and define port
    cluster_name = sys.argv[1]
    server_port = int(sys.argv[2])
    server_hostname = socket.gethostname()
    server_str = f"{server_hostname}:{server_port}"

    # Create the consistent hasher which understands nodes and their hashes on the ring
    consistent_hasher = ConsistentHasher(replicas=3)

    # Create a coordinator that watches Zookeeper and updates the consistent hash with available nodes
    coordinator = ZookeeperCoordinator(ZK_HOSTS, f"{ZK_SERVICE_BASE}/{cluster_name}", consistent_hasher)

    # Create a falcon app to serve the KV and Metrics resources under the root route
    app = falcon.App()
    app.req_options.auto_parse_form_urlencoded=True
    app.add_route('/kv/{key}', KVResource(server_str, consistent_hasher))
    app.add_route('/metrics', MetricsResource())

    # Serve the falcon app, after registering this server with Zookeeper and the consistent hasher
    try:
        print("Starting server...")
        coordinator.register_node(server_str)
        bjoern.run(app, '0.0.0.0', server_port)
    except Exception as e:
        print(f"EXCEPTION: {e}")
    finally:
        coordinator.unregister_node(server_str)
        coordinator.shutdown()

