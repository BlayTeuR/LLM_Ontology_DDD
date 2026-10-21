# Neo4j knowledge graph

Stores the generated artifacts (`.ttl`) in a Neo4j graph, with the [neosemantics (n10s)](https://neo4j.com/labs/neosemantics/) plugin.

## Start Neo4j

Run from the repository root. `docker-compose.yaml` reads the password from a `.env` file next to it:

```
NEO4J_PASSWORD=<your password>
```

```
docker compose up -d
```

Neo4j Browser: http://localhost:7474 (user `neo4j`, Bolt on port 7687). The data is kept in the Docker volume `neo4j_data`. The password is applied only when the volume is created: changing `.env` afterwards does not change it.

## First-time setup

Run the two statements of [`init.cypher`](init.cypher) once in Neo4j Browser. They create a uniqueness constraint on `Resource.uri` and configure n10s (`handleVocabUris: "IGNORE"`, `handleMultival: "ARRAY"`, `handleRDFTypes: "LABELS"`).

## Load an artifact

```
python neo4j_knowledge_graph/load_ttl_to_neo4j.py examples/insurance/insurance.ttl
```

The password is read from `NEO4J_PASSWORD` in `.env`, or given with `--password`. The script reads the `ddd:sourceFile` values of the `.ttl` (the name of the source `.cml`, e.g. `insurance.cml`), deletes the nodes already loaded from these sources, then imports the file. Loading the same file twice therefore leaves the graph unchanged.

Check what is loaded, in Neo4j Browser:

```
MATCH (n) WHERE n.sourceFile IS NOT NULL
RETURN n.sourceFile AS sourceFile, count(*) AS nodes
```

For `insurance.cml`: `["insurance.cml"]`, 110 nodes.

## Good to know

- `sourceFile` is stored as a list (`handleMultival: "ARRAY"`).
- To remove the loaded data, use `MATCH (n) WHERE n.sourceFile IS NOT NULL DETACH DELETE n`. Do not delete every node: this would also delete the n10s configuration node.
- There is no inference in Neo4j: a `RootEntity` is not also an `Entity` there.
- The `TEAM` contexts are `:BoundedContext` nodes with `bcType = 'TEAM'`: filter with `WHERE bc.bcType <> 'TEAM'` to count the model contexts.
- The reasoner result does not block the loading yet: run the reasoner first (see [`reasoner/`](../reasoner)).
