import networkx as nx
from pyvis.network import Network
import tempfile
import os


# Color coding by entity type
# This makes the graph immediately readable at a glance
ENTITY_COLORS = {
    "Account Number": "#e74c3c",   # red — highest risk, direct financial identifier
    "Person Name":    "#3498db",   # blue — individual
    "Company":        "#2ecc71",   # green — business entity
    "Company/Person": "#9b59b6",   # purple — ambiguous, from news
    "Invoice Number": "#f39c12",   # orange — transaction reference
}

ENTITY_SIZES = {
    "Account Number": 30,
    "Person Name":    25,
    "Company":        25,
    "Company/Person": 25,
    "Invoice Number": 20,
}


def build_entity_graph(processed_docs: list) -> nx.Graph:
    """
    Reads all processed documents and builds a graph where:
    - Each unique entity value is a NODE (account number, name, company)
    - Two entities are connected by an EDGE if they appear in the same document
    - Edge weight increases if two entities co-occur across multiple documents
    
    This is the same co-occurrence graph methodology used in AML link analysis.
    """
    G = nx.Graph()

    for doc_index, doc in enumerate(processed_docs):
        doc_type = doc["doc_type"]
        extracted = doc["extracted"]
        doc_label = f"Doc {doc_index + 1}: {doc_type.replace('_', ' ').title()}"

        # Pull entities from each document type
        entities_in_doc = []

        if doc_type == "bank_statement":
            _add(entities_in_doc, "Account Number",
                 extracted.get("account_number"), doc_label)
            _add(entities_in_doc, "Person Name",
                 extracted.get("account_holder"), doc_label)
            # Also extract account numbers referenced inside transactions
            import re
            for txn in extracted.get("transactions", []):
                acct = re.search(r"\b\d{4}-\d{4}(?:-\d{4})?\b", txn)
                if acct:
                    _add(entities_in_doc, "Account Number",
                         acct.group(), doc_label)

        elif doc_type == "invoice":
            _add(entities_in_doc, "Company",
                 extracted.get("vendor_name"), doc_label)
            _add(entities_in_doc, "Company",
                 extracted.get("buyer_name"), doc_label)
            _add(entities_in_doc, "Invoice Number",
                 extracted.get("invoice_number"), doc_label)

        elif doc_type == "dispute_letter":
            _add(entities_in_doc, "Person Name",
                 extracted.get("claimant_name"), doc_label)
            _add(entities_in_doc, "Account Number",
                 extracted.get("account_number"), doc_label)

        elif doc_type == "news_snippet":
            for entity in extracted.get("entities_mentioned", []):
                _add(entities_in_doc, "Company/Person", entity, doc_label)

        # Add nodes to graph
        for entity_type, value, source_doc in entities_in_doc:
            if G.has_node(value):
                # Node exists — add this document to its appearance list
                G.nodes[value]["docs"].append(source_doc)
                G.nodes[value]["doc_count"] += 1
            else:
                G.add_node(
                    value,
                    entity_type=entity_type,
                    color=ENTITY_COLORS.get(entity_type, "#95a5a6"),
                    size=ENTITY_SIZES.get(entity_type, 20),
                    docs=[source_doc],
                    doc_count=1,
                    title=f"{entity_type}: {value}\nFound in: {source_doc}"
                )

        # Connect every pair of entities that appear in the same document
        # This is co-occurrence — the core of link analysis
        for i in range(len(entities_in_doc)):
            for j in range(i + 1, len(entities_in_doc)):
                node_a = entities_in_doc[i][1]
                node_b = entities_in_doc[j][1]
                if node_a == node_b:
                    continue
                if G.has_edge(node_a, node_b):
                    # Strengthen the edge — they co-occur again
                    G[node_a][node_b]["weight"] += 1
                    G[node_a][node_b]["docs"].append(doc_label)
                else:
                    G.add_edge(
                        node_a, node_b,
                        weight=1,
                        docs=[doc_label],
                        color="#7f8c8d"
                    )

    # After building: highlight cross-document nodes and edges in red
    # A node appearing in 2+ documents is a key investigative lead
    for node in G.nodes:
        if G.nodes[node]["doc_count"] > 1:
            G.nodes[node]["color"] = "#ff0000"
            G.nodes[node]["size"] = 40
            G.nodes[node]["title"] = (
                f"⚠️ CROSS-DOCUMENT ENTITY\n"
                f"{G.nodes[node]['entity_type']}: {node}\n"
                f"Appears in {G.nodes[node]['doc_count']} documents:\n"
                + "\n".join(set(G.nodes[node]["docs"]))
            )

    for u, v in G.edges:
        if G[u][v]["weight"] > 1:
            G[u][v]["color"] = "#ff0000"
            G[u][v]["width"] = G[u][v]["weight"] * 2

    return G


def _add(entity_list, entity_type, value, doc_label):
    """Helper — only add if value is real and not empty."""
    if value and str(value).strip().lower() not in ["none", "null", "", "n/a"]:
        entity_list.append((entity_type, str(value).strip(), doc_label))


def render_graph_html(G: nx.Graph) -> str:
    """
    Converts the NetworkX graph to an interactive Pyvis HTML string.
    Physics simulation makes it feel like a real investigation tool.
    Returns the HTML as a string for embedding in Streamlit.
    """
    if len(G.nodes) == 0:
        return None

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#0e1117",      # matches Streamlit dark theme
        font_color="#ffffff",
        notebook=False
    )

    # Physics settings — Barnes-Hut is the standard for network graphs
    # Makes nodes repel each other so the graph is readable
    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=150,
        spring_strength=0.05,
        damping=0.09
    )

    # Copy nodes and edges from NetworkX into Pyvis
    for node, attrs in G.nodes(data=True):
        net.add_node(
            node,
            label=node,
            color=attrs.get("color", "#95a5a6"),
            size=attrs.get("size", 20),
            title=attrs.get("title", node),
            font={"size": 12, "color": "#ffffff"}
        )

    for u, v, attrs in G.edges(data=True):
        net.add_edge(
            u, v,
            color=attrs.get("color", "#7f8c8d"),
            width=attrs.get("weight", 1),
            title="\n".join(attrs.get("docs", []))
        )

    # Write to a temp file and read back as string
    # Streamlit needs an HTML string, not a file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w"
    ) as f:
        net.save_graph(f.name)
        tmp_path = f.name

    with open(tmp_path, "r") as f:
        html_content = f.read()

    os.unlink(tmp_path)
    return html_content


def get_graph_stats(G: nx.Graph) -> dict:
    """
    Returns summary statistics about the graph.
    These numbers are what you cite in the interview.
    """
    if len(G.nodes) == 0:
        return {}

    cross_doc_nodes = [
        n for n in G.nodes if G.nodes[n]["doc_count"] > 1
    ]

    # Most connected node = highest degree centrality
    # In AML this is the entity that links the most other entities
    # Classic money mule or shell company signal
    degree_centrality = nx.degree_centrality(G)
    most_connected = max(degree_centrality, key=degree_centrality.get) \
        if degree_centrality else None

    return {
        "total_nodes": len(G.nodes),
        "total_edges": len(G.edges),
        "cross_doc_entities": len(cross_doc_nodes),
        "cross_doc_names": cross_doc_nodes,
        "most_connected_entity": most_connected,
        "most_connected_score": round(
            degree_centrality.get(most_connected, 0), 3
        ) if most_connected else 0,
        "isolated_nodes": len(list(nx.isolates(G)))
    }