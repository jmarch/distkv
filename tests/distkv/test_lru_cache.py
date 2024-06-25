from distkv.lru_cache import LRUCache


def test_cache() -> None:
    CAPACITY = 3

    cache = LRUCache(capacity=CAPACITY)

    cache.put('one_key', 'one_value')
    cache.put('two_key', 'two_value')
    cache.put('three_key', 'three_value')

    # assert values put in the cache can be retrieved
    assert cache.get('one_key') == 'one_value'
    assert cache.get('two_key') == 'two_value'
    assert cache.get('three_key') == 'three_value'

    # assert LRU list is in order of least to most recently accessed
    assert cache.lru() == 'one_key,two_key,three_key'

    cache.put('two_key', 'two_new_value')

    # assert two_key value was appropriately overwritten
    assert cache.get('two_key') == 'two_new_value'

    # assert overriding two_key with new value moves two_key to most recently accessed
    assert cache.lru() == 'one_key,three_key,two_key'

    cache.put('four_key', 'four_value')

    # assert four_key value was appropriately written, eviction should have made space
    assert cache.get('four_key') == 'four_value'

    cache.put('five_key', 'five_value')

    # assert five_key value was appropriately written, eviction should have made space
    assert cache.get('five_key') == 'five_value'

    # assert adding two new keys evicts two least recently accessed
    assert cache.lru() == 'two_key,four_key,five_key'

    # assert two evicted keys are no longer available
    assert cache.get('one_key') is None
    assert cache.get('three_key') is None

    # assert capacity constraint still holds
    assert len(cache.lru().split(',')) == CAPACITY

