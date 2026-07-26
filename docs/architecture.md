# Architecture

## First vertical slice

```text
CLI
 └─ ScheduleClient
     ├─ immutable raw HTML snapshot
     └─ ProgrammaTileorasis parser
         └─ Pydantic Broadcast records
             └─ idempotent DuckDB upsert
```

The source page is addressed by channel ID, channel name, and broadcast date. The
parser selects only the matching channel table and ignores navigation rows. When the
displayed times wrap from late evening to early morning, subsequent broadcasts are
assigned to the next calendar day in the `Europe/Athens` timezone.

## Data boundary

`Broadcast` represents a source observation, not yet a canonical film or television
programme. Its stable identity is derived from channel, start time, title, and source
URL. Later enrichment will introduce a separate canonical programme entity instead
of overwriting source data.

Raw snapshots are excluded from Git because they can be regenerated and may contain
large amounts of third-party content. A reduced fixture documents the upstream HTML
contract and makes parser tests reproducible.
