"""TTL -> Neo4j en une commande (depuis la racine du depot).
    Utilisation : python neo4j_knowledge_graph/load_ttl_to_neo4j.py <fichier.ttl> [--password <mot de passe>]
    Sans --password, le mot de passe est lu dans NEO4J_PASSWORD (fichier .env).
    Exemple : python neo4j_knowledge_graph/load_ttl_to_neo4j.py examples/insurance/insurance.ttl
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
    """Valeurs de ddd:sourceFile présentes dans le TTL, ex. {'insurance.cml'}."""
    g = Graph()
    g.parse(ttl_path, format="turtle")
    return sorted({str(o) for _, p, o in g if str(p).endswith("sourceFile")})

def replace_source(session, ttl_text, source_files):
    """Supprime de Neo4j les anciens nœuds de ces fichiers sources, puis importe le TTL à la place (rechargement propre)"""    
    for f in source_files:
        session.run("MATCH (n) WHERE $f IN n.sourceFile DETACH DELETE n", f=f)
    # 2. importer le TTL (envoyé comme texte, sans chemin de fichier Docker)
    rec = session.run("CALL n10s.rdf.import.inline($rdf, 'Turtle')", rdf=ttl_text).single()
    if rec["terminationStatus"] != "OK":
        raise RuntimeError(f"Import n10s en échec : {rec['extraInfo']}")
    return rec["triplesLoaded"]

def main():
    parser = argparse.ArgumentParser(description='Load a TTL file into Neo4j.')
    parser.add_argument('ttl_file', help='TTL file to load into Neo4j')
    parser.add_argument('--password', help='Database password for Neo4j', default=DEFAULT_PASSWORD)
    args = parser.parse_args()

    password = args.password or os.getenv("NEO4J_PASSWORD")
    if not password:
        print("Erreur : mot de passe absent (--password ou NEO4J_PASSWORD).", file=sys.stderr)
        return 1
    if not os.path.isfile(args.ttl_file):
        print(f"Erreur : fichier introuvable : {args.ttl_file}", file=sys.stderr)
        return 1

    sources = read_source_files(args.ttl_file)
    if not sources:
        print("Erreur : aucun ddd:sourceFile dans le TTL, rechargement impossible.", file=sys.stderr)
        return 1
    with open(args.ttl_file, encoding="utf-8") as f:
        ttl_text = f.read()

    # Tentative de connexion à Neo4j et chargement du fichier TTL
    with GraphDatabase.driver(URI, auth=("neo4j", password)) as driver:
        try:
            driver.verify_connectivity()
        except Exception as e:
            print(f"Erreur : connexion à Neo4j impossible (Docker lancé ? mot de passe ?) : {e}",
                  file=sys.stderr)
            return 1
        try:
            with driver.session() as session:
                n = replace_source(session, ttl_text, sources)
        except Exception as e:
            print(f"Erreur pendant le chargement : {e}", file=sys.stderr)
            return 1

    print(f"{n} triplets chargés pour {', '.join(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())