"""TTL -> Neo4j in a single command (from the repository root).
    Usage: python neo4j_knowledge_graph/load_ttl_to_neo4j.py <file.ttl> [--password <password>]
    Without --password, the password is read from NEO4J_PASSWORD (.env file).
    Example: python neo4j_knowledge_graph/load_ttl_to_neo4j.py examples/insurance/insurance.ttl
"""

import argparse
import os
import sys

from neo4j import GraphDatabase, basic_auth
from rdflib import Graph

from dotenv import load_dotenv
load_dotenv()

DEFAULT_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")  # Default password if not provided
URI = "bolt://localhost:7687"

def read_source_files(ttl_path):
    """ddd:sourceFile values present in the TTL, e.g. {'insurance.cml'}."""
    g = Graph()
    g.parse(ttl_path, format="turtle")
    return sorted({str(o) for _, p, o in g if str(p).endswith("sourceFile")})

def replace_source(session, ttl_text, source_files):
    """Delete from Neo4j the old nodes of these source files, then import the TTL in their place (clean reload)."""
    for f in source_files:
        session.run("MATCH (n) WHERE $f IN n.sourceFile DETACH DELETE n", f=f)
    # 2. import the TTL (sent as text, without a Docker file path)
    rec = session.run("CALL n10s.rdf.import.inline($rdf, 'Turtle')", rdf=ttl_text).single()
    if rec["terminationStatus"] != "OK":
        raise RuntimeError(f"n10s import failed: {rec['extraInfo']}")
    return rec["triplesLoaded"]

def main():
    parser = argparse.ArgumentParser(description='Load a TTL file into Neo4j.')
    parser.add_argument('ttl_file', help='TTL file to load into Neo4j')
    parser.add_argument('--password', help='Database password for Neo4j', default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    password = args.password or os.getenv("NEO4J_PASSWORD")
    if not password:
        print("Error: missing password (--password or NEO4J_PASSWORD).", file=sys.stderr)
        return 1
    if not os.path.isfile(args.ttl_file):
        print(f"Error: file not found: {args.ttl_file}", file=sys.stderr)
        return 1

    sources = read_source_files(args.ttl_file)
    if not sources:
        print("Error: no ddd:sourceFile in the TTL, reload impossible.", file=sys.stderr)
        return 1
    with open(args.ttl_file, encoding="utf-8") as f:
        ttl_text = f.read()

    # Try to connect to Neo4j and load the TTL file
    with GraphDatabase.driver(URI, auth=("neo4j", password)) as driver:
        try:
            driver.verify_connectivity()
        except Exception as e:
            print(f"Error: cannot connect to Neo4j (Docker running? password?): {e}",
                  file=sys.stderr)
            return 1
        try:
            with driver.session() as session:
                n = replace_source(session, ttl_text, sources)
        except Exception as e:
            print(f"Error during loading: {e}", file=sys.stderr)
            return 1

    print(f"{n} triples loaded for {', '.join(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())