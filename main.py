import itertools
import json
import time
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from pyvis.network import Network
from rdflib import Graph, URIRef
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

import HtmlTemplate
from TripleStore import TripleStore

app = FastAPI()
store = TripleStore()
store_source = 'vkb_sample.ttl'
store.get_graph(store_source)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/opstelling/{asset_id}/visualize", response_class=HTMLResponse)
async def get_asset(asset_id: str = ''):
    start = time.time()
    asset_ids = store.get_all_related_assets(URIRef('https://data.awvvlaanderen.be/id/asset/' + asset_id))

    triples = []
    for l_asset_id in asset_ids:
        triples.extend(list(store.get_asset_triples(asset_id=l_asset_id)))

    end = time.time()
    time_spent = round(end - start, 2)
    print(f'Time to process query: {time_spent}')

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

    triple_lines = []
    triple_count = 0
    for s, p, o in triples:
        triple_count += 1
        triple_lines.append('{subject:"' + str(s) + '", predicate:"' + str(p) + '", object:"' + str(o) + '"},')

    html_content = HtmlTemplate.html_template_string
    html_content = html_content.replace('$$$triples$$$', '\n'.join(triple_lines))
    html_content = html_content.replace('$time_spent$', str(time_spent))
    html_content = html_content.replace('$triple_count$', str(triple_count))

    return HTMLResponse(content=html_content)


@app.get("/opstelling/{asset_id}/visualize2", response_class=HTMLResponse)
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

    end = time.time()
    time_spent = round(end - start, 2)
    print(f'Time to process query: {time_spent}')

    net = Network(directed=True, height='870px')

    triple_count = 0
    for s, p, o in triples:
        triple_count += 1
        str_s = str(s)
        str_o = str(o)
        if str_s not in net.node_ids:
            if str_s.startswith('https://data.awvvlaanderen.be/id/asset/'):
                net.add_node(n_id=str_s, color='#66ff69',
                             label=str_s.replace('https://data.awvvlaanderen.be/id/asset/', ''))
            else:
                net.add_node(n_id=str_s)
        if str_o not in net.node_ids:
            if str(p) == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                net.add_node(n_id=str_o, color='#ff675c')
            else:
                net.add_node(n_id=str_o)
        net.add_edge(str_s, str_o, title=p)

    net.toggle_physics(True)
    html_content = net.generate_html()

    html_content = html_content.replace(
        '</body>', f'<p>Time spent to perform query: found {triple_count} triples in {time_spent} seconds</p></body>')

    return HTMLResponse(content=html_content)


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
                        font-size: 0.95em;
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


class Format(str, Enum):
    ttl = 'ttl'
    turtle = 'turtle'
    json = 'json'
    jsonld = 'jsonld'


@app.get("/opstelling/", response_class=ORJSONResponse)
async def get_asset(asset_id: str, format: Format):
    asset_ids = store.get_all_related_assets(URIRef('https://data.awvvlaanderen.be/id/asset/' + asset_id))

    triples = []
    for l_asset_id in asset_ids:
        triples.extend(list(store.get_asset_triples(asset_id=l_asset_id)))
    if len(triples) == 0:
        raise HTTPException(status_code=404, detail=f"Asset with id {asset_id} not found")

    h = Graph()
    for triple in triples:
        h.add(triple)

    if format in [Format.json, Format.jsonld]:
        json_content = h.serialize(format='json-ld')
        return ORJSONResponse(json.loads(json_content))
    elif format in [Format.ttl, Format.turtle]:
        ttl_content = h.serialize(format='turtle')
        return Response(ttl_content)


@app.get("/asset/", response_class=ORJSONResponse)
async def get_asset(asset_id: str, format: str):
    triples = store.get_asset_triples(asset_id=asset_id)
    first = next(triples, None)
    if first is None:
        raise HTTPException(status_code=404, detail=f"Asset with id {asset_id} not found")

    h = Graph()
    for triple in itertools.chain([first], triples):
        h.add(triple)

    if format in ['json', 'jsonld', 'json-ld']:
        json_content = h.serialize(format='json-ld')
        return ORJSONResponse(json.loads(json_content))
    elif format in ['ttl', 'turtle']:
        ttl_content = h.serialize(format='turtle')
        return Response(ttl_content)

# uvicorn main:app --reload

# https://fastapi.tiangolo.com/tutorial/first-steps/
