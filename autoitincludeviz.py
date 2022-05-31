import argparse as ap
import os
import pathlib as pl
import re
from typing import List, Tuple

import networkx as nx
import pyvis.network as pvnet


INCLUDE_ONCE_PATTERN: re.Pattern = re.compile(
    r'^#include-once', 
    flags=re.MULTILINE)
INCLUDE_PATTERN: re.Pattern = re.compile(
    r'^#include "([\w.\\]+\.au3)"', 
    flags=re.MULTILINE)

def get_all_includes(filepath: str) -> Tuple[bool, List[str]]:
    with open(filepath, "r", encoding="utf8", errors="ignore") as file:
        contents = file.read()
        include_once: bool = INCLUDE_ONCE_PATTERN.search(contents) is not None
        all_includes: List[str] = [
            (pl.Path(filepath).parent / include.replace("\\", os.path.sep)).resolve() 
            for include in INCLUDE_PATTERN.findall(contents)]
    
    return include_once, all_includes

def create_include_edges(filename: str, includes: List[str]) -> List[Tuple[str, str]]:
    include_edges = [(include, filename) for include in includes]
    
    return include_edges
  
def construct_graph(starting_dir: str, excluded_filenames: List[str] = []) -> nx.DiGraph:
    starting_dir_path: pl.Path = pl.Path(starting_dir).resolve() 

    dep_graph = nx.DiGraph()
    
    all_autoit_filepaths: List[pl.Path] = [
        path.resolve() for path in pl.Path(starting_dir).rglob("*.au3")
        if path.resolve().name not in excluded_filenames]
    
    for autoit_filepath in all_autoit_filepaths:
        _, all_includes = get_all_includes(str(autoit_filepath))
        include_edges: List[Tuple[str, str]] = create_include_edges(
            str(autoit_filepath).removeprefix(
                str(starting_dir_path) + os.path.sep), 
            [str(include).removeprefix(
                str(starting_dir_path) + os.path.sep) 
             for include in all_includes])
        
        dep_graph.add_node(
            str(autoit_filepath).removeprefix(
                str(starting_dir_path) + os.path.sep))
        
        dep_graph.add_edges_from(include_edges)
    
    return dep_graph

def main():
    parser: ap.ArgumentParser = ap.ArgumentParser(
        description="Create a graph of dependencies for an AutoIt project.")
    parser.add_argument("proj_dir", type=str, 
                        help="the root of the AutoIt project")
    parser.add_argument("--output-path", "-o", type=str, default="dependencies.html",
                        help="path at which to write the html output")
    parser.add_argument("--exclude-filename", "-e", type=str, action="append", 
                        help="filenames (not paths) to exclude from consideration")
    
    args = parser.parse_args()
    
    dep_graph: nx.DiGraph = construct_graph(args.proj_dir, args.exclude_filename)
    for node in dep_graph.nodes:
        dep_graph.nodes[node]["color"] = "green"
    
    try:
        cycle = nx.find_cycle(dep_graph, orientation="original")
        print(f"Found Dependency Cycle: {cycle}")
        bad_nodes = list(set([node for node, _, _ in cycle]))
        for node in bad_nodes:
            dep_graph.nodes[node]["color"] = "red"
    except:
        print(f"No dependency cycles found.")
    finally:    
        dep_net: pvnet.Network = pvnet.Network(notebook=True, directed=True)
        dep_net.from_nx(dep_graph)
    
        dep_net.show(args.output_path)

if __name__ == "__main__":
    main()