# LLM Ontology DDD

A Hybrid LLM–Ontology Approach for Constructing the Ubiquitous Language and Resolving Semantic Conflicts in Domain-Driven Design

| Tool | What | Example |
|---|---|---|
| [**CML to OWL (.ttl)**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/cml_to_ttl) | Converts a Context Mapper file (.cml) into an OWL artifact (.ttl) conforming to the DDD metamodel (ddd-metamodel.ttl, version 0.2.0). No LLM involved: the conversion is deterministic. | `python cml_to_ttl/src/main_cml_to_ttl.py examples/insurance/insurance.cml` |
| [**Reasoner (HermiT)**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/reasoner) | Checks the logical consistency of an artifact (.ttl) against the DDD metamodel with the HermiT reasoner (via Owlready2). Includes negative tests that inject errors into a valid artifact. First version: one file at a time, run manually. | `python reasoner/reason.py examples/insurance/insurance.ttl` |
| [**Neo4j knowledge graph**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/neo4j_knowledge_graph) | Loads the generated artifacts (.ttl) into a Neo4j graph (neosemantics). Loading a file replaces the nodes previously loaded from the same source `.cml`. | `python neo4j_knowledge_graph/load_ttl_to_neo4j.py examples/insurance/insurance.ttl` |
| [**Metamodel**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/metamodel) | The DDD metamodel: current version (`ddd-metamodel.ttl`, 0.2.0), its SHACL rules (`shapes.ttl`) and the archived previous versions. Read by the reasoner; the artifacts produced by the converter conform to it. | / |
| [**Examples**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/examples) | Reference input and output of the pipeline (the Insurance example from Context Mapper). | / |

## Requirements

- Java and Python 3.x; install the Python dependencies with `pip install -r requirements.txt`.
- [Context Mapper CLI](https://contextmapper.org) 6.12.0 (`cm`), installed separately and available in your `PATH`.
- Docker, only for the Neo4j step.

## Pipeline

Run every command from the repository root. The steps are run one by one: the reasoner result does not block the Neo4j loading yet.

```
python cml_to_ttl/src/main_cml_to_ttl.py examples/insurance/insurance.cml
python reasoner/reason.py cml_to_ttl/output_cml/ttl/insurance.ttl
docker compose up -d
python neo4j_knowledge_graph/load_ttl_to_neo4j.py cml_to_ttl/output_cml/ttl/insurance.ttl
```

1. CML → Turtle: writes the generated files in `cml_to_ttl/output_cml/` (not versioned).
2. HermiT consistency check of the generated `.ttl`.
3. Neo4j: needs `NEO4J_PASSWORD` in a `.env` file at the repository root. See [`neo4j_knowledge_graph/README.md`](neo4j_knowledge_graph/README.md) for the first-time setup.

`examples/insurance/insurance.ttl` is a ready-made copy of the step 1 output: use it to try steps 2 and 3 without running the converter.

## Authors

- Bastien Jallais
- Jameleddine Hassine
