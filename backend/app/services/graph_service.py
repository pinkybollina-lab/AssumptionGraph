
import networkx as nx

from sqlalchemy.orm import Session

from ..models import Assumption, Dependency


def build_assumption_graph(db: Session) -> nx.DiGraph:
    """
    Build a directed graph using saved assumptions and
    explicitly recorded dependencies.

    DEPENDS_ON convention:
    from_assumption_id = dependent assumption
    to_assumption_id = prerequisite assumption

    Graph direction:
    prerequisite -> dependent
    This makes downstream impact traversal easier.
    """

    graph = nx.DiGraph()

    assumptions = db.query(Assumption).all()
    dependencies = db.query(Dependency).all()

    # Create one node for every saved assumption.
    for item in assumptions:
        graph.add_node(
            item.id,
            department=item.department,
            subject=item.subject,
            metric=item.metric,
            value=item.value,
            unit=item.unit,
            period=item.period,
            assumption_type=item.assumption_type,
            evidence=item.evidence,
            extraction_confidence=item.extraction_confidence,
            review_status=item.review_status,
        )

    # Add only dependencies explicitly stored in the database.
    for dependency in dependencies:

        source_id = dependency.from_assumption_id
        target_id = dependency.to_assumption_id
        relation = (dependency.relation or "").upper()

        if source_id not in graph or target_id not in graph:
            continue

        if relation == "DEPENDS_ON":
            # Prerequisite -> dependent
            graph.add_edge(
                target_id,
                source_id,
                relation=relation,
                rationale=dependency.rationale,
            )
        else:
            graph.add_edge(
                source_id,
                target_id,
                relation=relation,
                rationale=dependency.rationale,
            )

    return graph


def get_graph_data(db: Session) -> dict:
    """Return graph nodes, edges, and basic graph statistics."""

    graph = build_assumption_graph(db)

    nodes = [
        {
            "id": node_id,
            **attributes,
        }
        for node_id, attributes in graph.nodes(data=True)
    ]

    edges = [
        {
            "source": source,
            "target": target,
            **attributes,
        }
        for source, target, attributes in graph.edges(data=True)
    ]

    return {
        "success": True,
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "is_directed": graph.is_directed(),
        "has_cycles": not nx.is_directed_acyclic_graph(graph),
        "nodes": nodes,
        "edges": edges,
    }


def get_downstream_impacts(
    db: Session,
    assumption_id: int
) -> list:
    """Find assumptions downstream of a changed assumption."""

    graph = build_assumption_graph(db)

    if assumption_id not in graph:
        return []

    affected_ids = nx.descendants(graph, assumption_id)

    return [
        {
            "id": node_id,
            **graph.nodes[node_id],
        }
        for node_id in affected_ids
    ]


def get_downstream_paths(
    db: Session,
    assumption_id: int,
    max_depth: int = 10,
    max_paths: int = 100,
) -> list:
    """
    Return explainable paths from an assumption to its
    downstream assumptions.

    Only explicitly saved dependencies are included.
    Paths are cycle-safe and bounded by depth and count.
    """

    graph = build_assumption_graph(db)

    if assumption_id not in graph:
        return []

    paths = []

    # Sort targets to make the output predictable.
    downstream_ids = sorted(
        nx.descendants(graph, assumption_id)
    )

    for target_id in downstream_ids:

        if len(paths) >= max_paths:
            break

        for path in nx.all_simple_paths(
            graph,
            source=assumption_id,
            target=target_id,
            cutoff=max_depth,
        ):
            assumptions = [
                {
                    "id": node_id,
                    **graph.nodes[node_id],
                }
                for node_id in path
            ]

            steps = []

            for source_id, target_node_id in zip(
                path, path[1:]
            ):
                edge_data = graph.get_edge_data(
                    source_id,
                    target_node_id,
                ) or {}

                steps.append({
                    "from_assumption_id": source_id,
                    "to_assumption_id": target_node_id,
                    "from_subject": graph.nodes[source_id]["subject"],
                    "to_subject": graph.nodes[target_node_id]["subject"],
                    "relation": edge_data.get("relation"),
                    "rationale": edge_data.get("rationale"),
                })

            paths.append({
                "assumption_ids": path,
                "assumptions": assumptions,
                "steps": steps,
                "depth": len(path) - 1,
            })

            if len(paths) >= max_paths:
                break

    return paths
