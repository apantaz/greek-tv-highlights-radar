# Architecture

## Ingestion architecture

```text
CLI
 └─ Ingestion orchestrator
     ├─ ingestion_runs: running
     ├─ ScheduleClient: bounded retry
     ├─ immutable raw snapshot: channel/date/run_id.html
     ├─ ProgrammaTileorasis parser
     ├─ schedule quality checks
     └─ atomic persistence
         ├─ broadcast_observations: append-only
         └─ ingestion_runs: succeeded or failed

latest successful run per source/channel/date
 └─ current_broadcasts view
```

The source page is addressed by channel ID, channel name, and broadcast date. The
parser selects only the matching channel table and ignores navigation rows. When the
displayed times wrap from late evening to early morning, subsequent broadcasts are
assigned to the next calendar day in the `Europe/Athens` timezone.

## Data grains

See the [data model](data-model.md) for the current entity-relationship diagram and
view lineage.

- `ingestion_runs`: one attempted fetch for one source, channel, and requested date.
- `broadcast_observations`: one programme row observed in one ingestion run.
- `current_broadcasts`: programmes from the latest successful run for each
  source/channel/date partition.
- `broadcasts`: preserved milestone-one table; migrated non-destructively and retained
  for audit compatibility.

`Broadcast` is still a source observation, not a canonical film or television
programme. Later enrichment will introduce a separate canonical programme entity
instead of overwriting source data.

## Failure boundary

The run record is created before network access. Fetch, snapshot, parse, quality, or
persistence errors close it as `failed` with a bounded error message. Observations and
the successful status update share one database transaction, preventing a run from
being marked successful with partial observations.

Raw snapshots are excluded from Git because they may contain large amounts of
third-party content. Each response is stored under its run identifier and is never
overwritten. A reduced fixture documents the upstream HTML contract and makes parser
tests reproducible.
