from unittest import TestCase

from rdflib import Graph, URIRef

from TripleStore import TripleStore
from main import get_asset, root


class GetAssetTests(TestCase):
    async def test_get_asset(self):
        asset = await get_asset(asset_id='1000000_bord_1771813')
        print(asset)

    async def test_root(self):
        asset = await root()
        print(asset)

    def test_get_asset_triples(self):
        store = TripleStore()
        store.get_graph('vkb_sample.ttl')

        asset_id = '1000007'

        result_triples = store.get_asset_triples(asset_id)
        for s, p, o in result_triples:
            print(f'{s} {p} {o}')

    def test_get_all_related_assets(self):
        store = TripleStore()
        store.get_graph('vkb_sample.ttl')

        asset_id = '1000007'
        asset_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{asset_id}')
        result_assets = store.get_all_related_assets(asset_ref)
        print(result_assets)
