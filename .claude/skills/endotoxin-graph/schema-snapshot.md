# Graph schema snapshot (auto-generated)

_Regenerated from the live graph by `kg.explore --write` after each load._
_Do not hand-edit; prefer `python -m kg.explore --schema` for live ground-truth._

## Node labels

- `:Condition` — 70
- `:Claim` — 53
- `:Evidence` — 53
- `:AtomicClaim` — 41
- `:Product` — 30
- `:Reagent` — 30
- `:Method` — 24
- `:LAL` — 18
- `:Company` — 18
- `:RegulatoryDocument` — 16
- `:CompendialMethod` — 16
- `:Preparation` — 15
- `:NarrativeClaim` — 12
- `:Patent` — 11
- `:Author` — 10
- `:Region` — 10
- `:Segment` — 6
- `:rCR` — 6
- `:rFC` — 5
- `:ExtractionActivity` — 2
- `:Document` — 2
- `:Article` — 2
- `:Institution` — 2
- `:Organism` — 2
- `:Bacteriophage` — 1

## Relationship types

- `-[:COMPARES]->` — 123
- `-[:RECOGNIZES]->` — 101
- `-[:UNDER]->` — 76
- `-[:SERVES_SEGMENT]->` — 73
- `-[:REPORTS]->` — 53
- `-[:ASSERTS]->` — 53
- `-[:WAS_DERIVED_FROM]->` — 53
- `-[:IN_FORCE_IN]->` — 37
- `-[:MANUFACTURES]->` — 30
- `-[:APPLIES_TO]->` — 20
- `-[:DECOMPOSES_TO]->` — 20
- `-[:HEADQUARTERED_IN]->` — 18
- `-[:REFERENCES]->` — 17
- `-[:PROTECTS]->` — 13
- `-[:PRODUCED_BY]->` — 12
- `-[:OWNS_PATENT]->` — 11
- `-[:AUTHORED]->` — 10
- `-[:AFFILIATED_WITH]->` — 10
- `-[:ACQUIRED]->` — 8
- `-[:PART_OF]->` — 7
- `-[:HARMONIZED_WITH]->` — 6
- `-[:ABOUT]->` — 5
- `-[:DESCRIBES]->` — 4
- `-[:HAS_PRESENCE_IN]->` — 4
- `-[:OWNS]->` — 3
- `-[:WAS_GENERATED_BY]->` — 2
- `-[:CITES]->` — 1

## Shape (how labels connect)

- `(:Claim)-[:COMPARES]->(:Preparation)` — 123
- `(:CompendialMethod)-[:RECOGNIZES]->(:Product)` — 101
- `(:Evidence)-[:UNDER]->(:Condition)` — 76
- `(:Product)-[:SERVES_SEGMENT]->(:Segment)` — 73
- `(:Document)-[:REPORTS]->(:Evidence)` — 53
- `(:Evidence)-[:ASSERTS]->(:Claim)` — 53
- `(:Evidence)-[:WAS_DERIVED_FROM]->(:Document)` — 53
- `(:Company)-[:MANUFACTURES]->(:Product)` — 30
- `(:RegulatoryDocument)-[:IN_FORCE_IN]->(:Region)` — 21
- `(:RegulatoryDocument)-[:APPLIES_TO]->(:Segment)` — 20
- `(:Claim)-[:DECOMPOSES_TO]->(:Claim)` — 20
- `(:Company)-[:HEADQUARTERED_IN]->(:Region)` — 18
- `(:RegulatoryDocument)-[:REFERENCES]->(:CompendialMethod)` — 17
- `(:CompendialMethod)-[:IN_FORCE_IN]->(:Region)` — 16
- `(:Patent)-[:PROTECTS]->(:Product)` — 13
- `(:Preparation)-[:PRODUCED_BY]->(:Method)` — 12
- `(:Company)-[:OWNS_PATENT]->(:Patent)` — 11
- `(:Author)-[:AUTHORED]->(:Document)` — 10
- `(:Company)-[:ACQUIRED]->(:Company)` — 8
- `(:Region)-[:PART_OF]->(:Region)` — 7
- `(:Author)-[:AFFILIATED_WITH]->(:Company)` — 6
- `(:CompendialMethod)-[:HARMONIZED_WITH]->(:CompendialMethod)` — 6
- `(:Document)-[:DESCRIBES]->(:Patent)` — 4
- `(:Author)-[:AFFILIATED_WITH]->(:Institution)` — 4
- `(:Company)-[:HAS_PRESENCE_IN]->(:Region)` — 4
- `(:Company)-[:OWNS]->(:Company)` — 3
- `(:Document)-[:WAS_GENERATED_BY]->(:ExtractionActivity)` — 2
- `(:Document)-[:ABOUT]->(:Product)` — 2
- `(:Document)-[:ABOUT]->(:Organism)` — 2
- `(:Document)-[:ABOUT]->(:Company)` — 1
- `(:Document)-[:CITES]->(:Document)` — 1
