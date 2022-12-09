import itertools
import json
import time
from collections.abc import Iterator

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from pyvis.network import Network
from rdflib import Graph, URIRef
from starlette.requests import Request
from starlette.responses import HTMLResponse

from TripleStore import TripleStore

app = FastAPI()
store = TripleStore()
store_source = 'vkb_sample.ttl'
store.get_graph(store_source)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/opstelling/{asset_id}", response_class=HTMLResponse)
async def get_asset(asset_id: str = ''):
    start = time.time()
    asset_ids = store.get_all_related_assets(URIRef('https://data.awvvlaanderen.be/id/asset/' + asset_id))

    triples = []
    for l_asset_id in asset_ids:
        triples.extend(list(store.get_asset_triples(asset_id=l_asset_id)))

    if len(triples) == 0:
        html_content = f"""
                <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
                <html>
                    <head>
                        <title>Opstelling information</title>
                    </head>
                    <body>
                        <h4>id {asset_id} matches no opstelling!</h4>
                    </body>
                </html>
                """
        return HTMLResponse(content=html_content)

    triple_table = """<table>
    <tr>
    <th>subject</th>
    <th>predicate</th>
    <th>object</th>
    </tr>"""

    for s, p, o in triples:
        if isinstance(s, URIRef):
            s = f'<a href="{s}">{s}</a>'
        if isinstance(p, URIRef):
            p = f'<a href="{p}">{p}</a>'
        if isinstance(o, URIRef):
            o = f'<a href="{o}">{o}</a>'
        triple_table += f"""
        <tr>
            <td>{s}</td>
            <td>{p}</td>
            <td>{o}</td>
        </tr>"""

    triple_table += """
    </table>"""

    html_content = """
        <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
        <html>
            <head>
                <title>Opstelling information</title>  
                <style>
                    table {
                        width: 100%;
                    }
                    table, th, td {
                        border: 1px solid;
                        border-collapse: collapse;
                    }
                </style>              
            </head>""" + f"""
            <body>
                <h2>opstelling {asset_id}</h2>
                <h4>Triple representation</h4>
                {triple_table}"""

    end = time.time()
    time_spent = round(end - start, 2)
    print(f'Time to process query: {time_spent}')
    html_content += f"""
        <p>Took {time_spent} seconds to generate</p>
        </body>
    </html>
    """

    net = Network(directed=True, height='800px')

    for s, p, o in triples:
        str_s = str(s)
        str_o = str(o)
        if str_s not in net.node_ids:
            net.add_node(n_id=str_s)
        if str_o not in net.node_ids:
            net.add_node(n_id=str_o)
        net.add_edge(str_s, str_o, title=p)

    net.toggle_physics(True)
    html_content = net.generate_html()

    return HTMLResponse(content=html_content)


@app.get("/asset/{asset_id}", response_class=HTMLResponse)
async def get_asset(asset_id: str = ''):
    triples = store.get_asset_triples(asset_id=asset_id)

    first = next(triples, None)
    if first is None:
        html_content = f"""
                <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
                <html>
                    <head>
                        <title>Asset information</title>
                    </head>
                    <body>
                        <h4>id {asset_id} matches no asset!</h4>
                    </body>
                </html>
                """
        return HTMLResponse(content=html_content)

    triple_table = """<table>
    <tr>
    <th>subject</th>
    <th>predicate</th>
    <th>object</th>
    </tr>"""

    for s, p, o in itertools.chain([first], triples):
        if isinstance(s, URIRef):
            s = f'<a href="{s}">{s}</a>'
        if isinstance(p, URIRef):
            p = f'<a href="{p}">{p}</a>'
        if isinstance(o, URIRef):
            o = f'<a href="{o}">{o}</a>'
        triple_table += f"""
        <tr>
            <td>{s}</td>
            <td>{p}</td>
            <td>{o}</td>
        </tr>"""

    triple_table += """
    </table>"""

    html_content = """
        <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
        <html>
            <head>
                <title>Asset information</title>  
                <style>
                    table {
                        width: 100%;
                    }
                    table, th, td {
                        border: 1px solid;
                        border-collapse: collapse;
                    }
                </style>              
            </head>""" + f"""
            <body>
                <h2>asset {asset_id}</h2>
                <h4>Triple representation</h4>
                {triple_table}
            </body>
        </html>
        """

    return HTMLResponse(content=html_content)


@app.get("/asset/", response_class=ORJSONResponse)
async def get_asset(asset_id: str, request: Request = None):
    if request.headers['accept'] != 'application/json':
        return None

    triples = store.get_asset_triples(asset_id=asset_id)
    first = next(triples, None)
    if first is None:
        raise HTTPException(status_code=404, detail=f"Asset with id {asset_id} not found")

    h = Graph()
    for triple in itertools.chain([first], triples):
        h.add(triple)

    json_content = h.serialize(format='json-ld')
    return ORJSONResponse(json.loads(json_content))

# uvicorn main:app --reload

# https://fastapi.tiangolo.com/tutorial/first-steps/
