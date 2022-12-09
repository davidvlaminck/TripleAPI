from tokenize import Triple
from typing import Generator, Set

from rdflib import Graph, URIRef, BNode


class TripleStore:
    def __init__(self):
        self._graph = None
        self._source = None

    def get_graph(self, source):
        if self._graph is None:
            self.load(source)
        else:
            if source != self._source:
                self.load(source)
        return self._graph

    def load(self, source):
        g = Graph()
        g.parse(source=source, format='turtle')
        self._graph = g
        self._source = source

    def get_asset_triples(self, asset_id: str) -> Generator:
        if self._graph is None:
            raise RuntimeError('There is no datasource loaded yet')

        asset_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{asset_id}')

        for s, p, o in self.yield_triples_found_by_subject(asset_ref):
            yield s, p, o

    def yield_triples_found_by_subject(self, asset_ref: [URIRef, BNode]):
        for s, p, o in self._graph.triples((asset_ref, None, None)):
            yield s, p, o
            if isinstance(o, BNode):
                for s1, p1, o1 in self.yield_triples_found_by_subject(o):
                    yield s1, p1, o1

    def get_all_related_assets(self, asset_ref: URIRef) -> Set[str]:
        if self._graph is None:
            raise RuntimeError('There is no datasource loaded yet')
        asset_identificator = str(asset_ref).replace('https://data.awvvlaanderen.be/id/asset/', '')
        assets_found = set()
        assets_found.add(asset_identificator)

        return self.get_all_related_assets_rec(asset_identificator, assets_found)

    def get_all_related_assets_rec(self, asset_str: str, assets_found: set = None) -> Set[str]:
        identificator_uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#DtcIdentificator.identificator'
        bron_uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#RelatieObject.bronAssetId'
        doel_uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#RelatieObject.doelAssetId'

        query = """SELECT ?o ?rel WHERE { ?di ?p1 ?s .
                                         ?rel ?p3 ?di .
                                         ?rel ?p2 ?bi .
                                         ?bi ?p1 ?o }"""
        query = query.replace('?s', '"' + asset_str + '"'). \
            replace('?p1', '<' + identificator_uri + '>'). \
            replace('?p2', '<' + bron_uri + '>'). \
            replace('?p3', '<' + doel_uri + '>')

        q_res = self._graph.query(query)
        for row in q_res:
            o_str = str(row.o)
            if o_str not in assets_found:
                assets_found.add(o_str)
                self.get_all_related_assets_rec(o_str, assets_found)

            rel_str = str(row.rel)
            print(rel_str)
            if rel_str not in assets_found:
                assets_found.add(rel_str.replace('https://data.awvvlaanderen.be/id/asset/', ''))

        query = """SELECT ?o ?rel WHERE { ?bi ?p1 ?s .
                                         ?rel ?p2 ?bi .
                                         ?rel ?p3 ?di .
                                         ?di ?p1 ?o }"""
        query = query.replace('?s', '"' + asset_str + '"'). \
            replace('?p1', '<' + identificator_uri + '>'). \
            replace('?p2', '<' + bron_uri + '>'). \
            replace('?p3', '<' + doel_uri + '>')

        q_res = self._graph.query(query)
        for row in q_res:
            o_str = str(row.o)
            if o_str not in assets_found:
                assets_found.add(o_str)
                self.get_all_related_assets_rec(o_str, assets_found)

            rel_str = str(row.rel)
            if rel_str not in assets_found:
                assets_found.add(rel_str.replace('https://data.awvvlaanderen.be/id/asset/', ''))

        return assets_found


