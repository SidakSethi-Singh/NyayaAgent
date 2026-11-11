# NyayaAgent — Corpus sources

All chunks are short summaries of public statutes, with the source recorded
per chunk in `data/corpus.jsonl` (`source_url`, `last_updated`).
`last_updated` is the date the chunk was curated/verified in this repo
(2026-11-11 for the v2 expansion), not the Act's amendment date.

## Acts in the corpus (71 chunks, 22 Acts)

| Act | Source |
|---|---|
| Constitution of India | India Code — https://www.indiacode.nic.in/handle/123456789/15240 |
| Transfer of Property Act, 1882 | India Code — https://www.indiacode.nic.in/handle/123456789/1362 |
| Consumer Protection Act, 2019 | India Code — https://www.indiacode.nic.in/handle/123456789/15256 |
| Information Technology Act, 2000 | India Code — https://www.indiacode.nic.in/handle/123456789/1366 |
| Digital Personal Data Protection Act, 2023 | India Code — https://www.indiacode.nic.in/handle/123456789/15639 |
| Bharatiya Nyaya Sanhita, 2023 | India Code — https://www.indiacode.nic.in/handle/123456789/15478 |
| Bharatiya Nagarik Suraksha Sanhita, 2023 | India Code — https://www.indiacode.nic.in/handle/123456789/15479 |
| Indian Contract Act, 1872 | India Code — https://www.indiacode.nic.in/handle/123456789/2188 |
| Companies Act, 2013 | India Code — https://www.indiacode.nic.in/handle/123456789/15252 |
| Right to Information Act, 2005 | India Code — https://www.indiacode.nic.in/handle/123456789/1350 |
| Motor Vehicles Act, 1988 (as amended 2019) | India Code — https://www.indiacode.nic.in/handle/123456789/1244 |
| Hindu Marriage Act, 1955 | India Code — https://www.indiacode.nic.in/handle/123456789/1511 |
| Negotiable Instruments Act, 1881 | India Code — https://www.indiacode.nic.in/handle/123456789/2189?sam_handle=123456789/1362 |
| Hindu Succession Act, 1956 | India Code — https://www.indiacode.nic.in/indiacode/handle/123456789/1713?view_type=browse |
| Indian Succession Act, 1925 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Registration Act, 1908 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Industrial Disputes Act, 1947 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Payment of Gratuity Act, 1972 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Maternity Benefit Act, 1961 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Minimum Wages Act, 1948 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Central Goods and Services Tax Act, 2017 | India Code portal — https://www.indiacode.nic.in/ (see note below) |
| Income-tax Act, 1961 | India Code portal — https://www.indiacode.nic.in/ (see note below) |

**Note on portal links:** for the last seven Acts, no per-act India Code
DSpace handle was verified, so the chunk's `source_url` points to the real
India Code portal homepage rather than an invented handle number. The Act
text is on the portal — search the Act name there. Inventing a handle
number would be a fake citation, which this project refuses to do.

## Rules

- No paywalled databases (SCC / Manupatra), no invented case citations.
- A citation that is not in the corpus is a failure, not a feature.
- Chunk texts are summaries — the agent quotes them as the corpus states
  them and never invents a section number, punishment, or case.
- Every chunk carries a `hi_summary`: a short Hindi summary, faithful to
  the English chunk text, so Hindi answers read in Hindi first.
- BNS/BNSS replaced IPC/CrPC on 1 July 2024 — the corpus labels this
  explicitly and never mixes old and new section numbers silently.
