# Convertisseur CML → Turtle (OWL)

Convertit un fichier Context Mapper (`.cml`) en artefact OWL (`.ttl`) conforme au métamodèle DDD (`ddd-metamodel.ttl`, version 0.3.0). Aucun LLM : la conversion est déterministe.

```
test.cml ──[ cm generate + export-json-v03.ftl ]──▶ output_cml/json/test.json ──[ cml2ttl.py ]──▶ output_cml/ttl/test.ttl
            (parseur officiel Context Mapper)                                    (mapping vers le métamodèle OWL)
```

## Prérequis

- Context Mapper CLI (`cm`) dans le `PATH`, Java 17+.
- Python 3 et `rdflib` : `python -m pip install rdflib`.

## Utilisation

```
python main_cml_to_ttl.py test.cml
```

Sortie : `output_cml/json/test.json` puis `output_cml/ttl/test.ttl` (même nom que le `.cml`). Autre dossier de sortie : `--out <dossier>`.

## Fichiers (tous dans le même dossier)

| Fichier | Rôle |
|---|---|
| `main_cml_to_ttl.py` | Point d'entrée : enchaîne les deux étapes |
| `cml_to_json.py` | Étape 1 : appelle `cm generate` avec le gabarit |
| `export-json-v03.ftl` | Gabarit Freemarker : recopie le CML en JSON, sans interprétation |
| `cml2ttl.py` | Étape 2 : JSON → graphe RDF (le mapping) |
| `iri.py` | Fabrication déterministe des IRI |

Pour valider l'artefact (SHACL, HermiT, Java requis), à part : `python cml2ttl.py output_cml/json/test.json -o x.ttl --validate [--no-hermit]`, avec `ddd-metamodel.ttl`, `shapes.ttl`, `validate_artifact.py`, `check_vocab.py` et `reason.py` dans le dossier.

## Ce qui est converti

| CML | OWL |
|---|---|
| `ContextMap`, `contains` | `ddd:ContextMap`, `showsRelevantContext` |
| `BoundedContext` | `ddd:BoundedContext` + `domainVisionStatement`, `responsibility` |
| `Domain`, `Subdomain` (CORE / SUPPORTING / GENERIC) | `ddd:Domain`, `CoreDomain` / `SupportingSubdomain` / `GenericSubdomain` |
| `Aggregate` | `ddd:Aggregate` |
| `Entity` (`aggregateRoot` ou non), `ValueObject`, `DomainEvent` | `RootEntity` / `Entity`, `ValueObject`, `DomainEvent` |
| attribut (`String nom`), référence (`- Type nom`) | `ddd:Attribute` ; une référence porte en plus `ddd:refersTo` vers le terme cible |
| `[U]->[D]` (+ `[S]`/`[C]`) | `UpstreamDownstreamRelationship` (`CustomerSupplierRelationship`) |
| `[P]<->[P]`, `[SK]<->[SK]` | `Partnership`, `SharedKernel` |
| rôles `OHS`, `PL`, `ACL`, `CF` | `OpenHostService`, `PublishedLanguage`, `AnticorruptionLayer`, `Conformist` |
| `exposedAggregates` | `ddd:exposesAggregate` |

Non converti (signalé ou absent du JSON) : contextes `TEAM`, Enum / Trait / DTO (avertissement), `import` (avertissement : exporter chaque fichier séparément), numéros de ligne, et les éléments absents du métamodèle V0 (`knowledgeLevel`, `implementationTechnology`, `useCases`, etc.).

## Tester

1. **Exécution** : `python main_cml_to_ttl.py insurance.cml`. Attendu : `609 triplets`, `Attribute=47`, `BoundedContext=6`, `Aggregate=10`, aucun avertissement.
2. **Comptes** (PowerShell) :
   ```
   (Select-String output_cml\ttl\insurance.ttl -Pattern "a ddd:Attribute").Count    # 47
   (Select-String output_cml\ttl\insurance.ttl -Pattern "ddd:refersTo").Count       # 18
   ```
3. **Déterminisme** : lancer deux fois et comparer `Get-FileHash` : les deux `.ttl` sont identiques.
4. **Sensibilité** : copier le `.cml`, ajouter un attribut à une entité, relancer : le TTL gagne un `Attribute` et rien d'autre ne change.
5. **Erreurs** : introduire une faute de syntaxe dans une copie : `cm` la signale et aucun JSON périmé n'est réutilisé.
6. **Autre fichier** : essayer un second `.cml` (exemple de la documentation Context Mapper) ; lire les avertissements.
