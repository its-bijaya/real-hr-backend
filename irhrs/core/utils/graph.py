"""@irhrs_docs"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def traverse(node, graph, visited=None, processing=None, ignored=None) -> set:
    """
    Traverse though a graph

    :param node:
        node in graph (a key in graph dict)

    :param graph:
        dictionary representing graph in linked list style
        node(key): [connected_nodes]
        eg. {
            1: [2, 3, 4, 5, 6, 7]
            2: [3, 4, 6]
            4: [9, 7]
        }

    :param visited: [Optional]
        dictionary kept by function to store visited nodes starting node as a key
        Pass an empty dictionary in visited if you want set of all possible nodes from a node.
        It will keep all the relations possible by staring from node.

    :param processing: [Optional]
        Set of nodes under processing maintained by the function

    :param ignored: [Optional]
        Store ignored nodes while processing, and will be processed if asked again

    * Note : Pass visited, processing and ignored if you want to preserve data after processing

    :return: set of all visited nodes

    """
    # store visited nodes to save computation
    visited = dict() if visited is None else visited
    ignored = defaultdict(set) if ignored is None else ignored
    processing = set() if processing is None else processing

    if node in visited:

        children = visited[node]

        for child in graph[node]:

            # if node has ignored any children previously because it was in processing, include it now
            if node in ignored and child in ignored[node] and child not in processing:
                children.update(traverse(child, graph, visited, processing, ignored))
                # remove ignored node because it is now included
                ignored[node].remove(child)

        return children

    # store processing nodes to prevent infinite recursion
    processing.add(node)

    children = set()

    if node in graph:
        children.update(graph[node])  # remove node from here

        for child in graph[node]:

            if child in processing:
                ignored[node].add(child)
            else:
                children.update(traverse(child, graph, visited, processing, ignored))

        if children:
            children = children - {node}
            visited[node] = children

    processing.remove(node)

    return children
