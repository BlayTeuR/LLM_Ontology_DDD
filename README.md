# LLL Ontology DDD

A Hybrid LLM–Ontology Approach for Constructing the Ubiquitous Language and Resolving Semantic Conflicts in Domain-Driven Design

| Tool | What | Example |
|---|---|---|
| [**CML to OWL (.ttl)**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/cml_to_ttl) | Converts a Context Mapper file (.cml) into an OWL artifact (.ttl) conforming to the DDD metamodel (ddd-metamodel.ttl, version 0.2.0). No LLM involved: the conversion is deterministic. | / |
| [**Reasoner (HermiT)**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/reasoner) | Checks the logical consistency of an artifact (.ttl) against the DDD metamodel with the HermiT reasoner (via Owlready2). Includes negative tests that inject errors into a valid artifact. First version: one file at a time, run manually. | `python reasoner/reason.py cml_to_ttl/output_cml/ttl/insurance.ttl` |
| [**Metamodel**](https://github.com/BlayTeuR/LLM_Ontology_DDD/tree/main/metamodel) | Folder that makes it possible to track the different versions of the metamodel (CML to OWL tool always use the most recent version of the metamodel) | / |

## Authors

- Bastien Jallais
- Jameleddine Hassine
