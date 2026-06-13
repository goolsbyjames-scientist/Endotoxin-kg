# BET graph — schema snapshot

> Orientation only. The graph changes — run `python -m kg.explore --schema` for
> current ground-truth. Snapshot captured 2026-06.

~145 nodes. Counts shown are at snapshot time.

## Node labels

| Count | Label | Notes |
|---|---|---|
| 29 | `:Product` (+`:Reagent` + chemistry) | a commercial assay/kit |
| 17 | `:LAL` | traditional Limulus Amebocyte Lysate products |
| 6 | `:rCR` | recombinant Cascade Reagent products |
| 5 | `:rFC` | recombinant Factor C products |
| 1 | `:Bacteriophage` | EndoLISA |
| 18 | `:Company` | manufacturers / owners |
| 16 | `:CompendialMethod` | pharmacopeia chapters (USP <85>, Ph. Eur. 2.6.32, …) |
| 16 | `:RegulatoryDocument` | FDA/agency guidances |
| 11 | `:Patent` | IP, keyed by `number` |
| 10 | `:Region` | ISO-coded; `PART_OF` hierarchy (country → continent) |
| 6 | `:Segment` | market segments (pharma, medical device, ATMP, …) |

Every product node carries three labels at once, e.g. `:Product:Reagent:rFC`.

## Relationships (how labels connect)

```
(:CompendialMethod)-[:RECOGNIZES]->(:Product)            101
(:Product)-[:SERVES_SEGMENT]->(:Segment)                  73
(:Company)-[:MANUFACTURES]->(:Product)                    29
(:RegulatoryDocument)-[:IN_FORCE_IN]->(:Region)           21
(:RegulatoryDocument)-[:APPLIES_TO]->(:Segment)           20
(:Company)-[:HEADQUARTERED_IN]->(:Region)                 18
(:RegulatoryDocument)-[:REFERENCES]->(:CompendialMethod)  17
(:CompendialMethod)-[:IN_FORCE_IN]->(:Region)             16
(:Patent)-[:PROTECTS]->(:Product)                         13
(:Company)-[:OWNS_PATENT]->(:Patent)                      11
(:Company)-[:ACQUIRED]->(:Company)                         8
(:Region)-[:PART_OF]->(:Region)                            7
(:CompendialMethod)-[:HARMONIZED_WITH]->(:CompendialMethod) 6
(:Company)-[:HAS_PRESENCE_IN]->(:Region)                   4
(:Company)-[:OWNS]->(:Company)                             3
```

## Common properties

- **Product/Reagent:** `id`, `name`, `chemistry`, `read_mode` (kinetic/endpoint),
  `format` (microplate/cartridge), `form`, `signal_type`, `family`,
  `year_introduced`, `status`, `notes`.
- **Company:** `id`, `name`, `type`, `status`, `notes`.
- **CompendialMethod:** `id`, `name`, `pharmacopoeia`, `chapter`, `title`,
  `category`, `effective_year`, `status`, and boolean `recognizes_*` flags
  (also modeled explicitly as `RECOGNIZES` edges).
- **RegulatoryDocument:** `id`, `name`, `title`, `issuing_body`, `doc_type`,
  `industry_segment`, `effective_year`, `last_updated_year`, `method_neutral`,
  `status`, `notes`.
- **Patent:** `id`, `number`, `title`, `jurisdiction`, `claim_category`,
  `claim_summary`, `priority_year`, `grant_year`, `expiration_year`, `status`.
- **Region:** `id`, `name`, `iso_code`, `scope`.
- **Segment:** `id`, `name`, `description`, `notes`.
