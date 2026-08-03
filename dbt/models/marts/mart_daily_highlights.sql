{{ config(materialized='table', tags=['aggregate', 'enrichment', 'highlights']) }}

with eligible_broadcasts as (
    select
        broadcasts.observation_id,
        broadcasts.channel_key,
        broadcasts.programme_key,
        broadcasts.source,
        broadcasts.channel,
        broadcasts.schedule_date,
        broadcasts.programme_position,
        broadcasts.title as schedule_title,
        broadcasts.starts_at_local,
        programmes.title as programme_title,
        programmes.original_title,
        programmes.release_year,
        programmes.imdb_id,
        programmes.genres_json,
        metrics.metric_observation_id,
        metrics.popularity,
        metrics.vote_average,
        metrics.vote_count,
        metrics.observed_at as metrics_observed_at
    from {{ ref('fct_current_broadcasts') }} as broadcasts
    inner join {{ ref('dim_programmes') }} as programmes
        on broadcasts.programme_key = programmes.programme_key
    inner join {{ ref('int_latest_tmdb_entity_metrics') }} as metrics
        on broadcasts.media_type = metrics.media_type
        and broadcasts.tmdb_id = metrics.tmdb_id
),

score_components as (
    select
        observation_id,
        channel_key,
        programme_key,
        source,
        channel,
        schedule_date,
        programme_position,
        schedule_title,
        starts_at_local,
        programme_title,
        original_title,
        release_year,
        imdb_id,
        genres_json,
        metric_observation_id,
        popularity,
        vote_average,
        vote_count,
        metrics_observed_at,
        round(least(100.0, greatest(0.0, coalesce(vote_average, 0.0) * 10.0)), 2)
            as quality_score,
        round(
            least(
                100.0,
                greatest(0.0, 20.0 * log10(greatest(coalesce(vote_count, 0), 0) + 1))
            ),
            2
        ) as confidence_score,
        round(
            least(
                100.0,
                greatest(0.0, 25.0 * log10(greatest(coalesce(popularity, 0.0), 0.0) + 1))
            ),
            2
        ) as popularity_score
    from eligible_broadcasts
),

scored as (
    select
        observation_id,
        channel_key,
        programme_key,
        source,
        channel,
        schedule_date,
        programme_position,
        schedule_title,
        starts_at_local,
        programme_title,
        original_title,
        release_year,
        imdb_id,
        genres_json,
        metric_observation_id,
        popularity,
        vote_average,
        vote_count,
        metrics_observed_at,
        quality_score,
        confidence_score,
        popularity_score,
        round(
            0.70 * quality_score
            + 0.20 * confidence_score
            + 0.10 * popularity_score,
            2
        ) as highlight_score
    from score_components
)

select
    observation_id,
    channel_key,
    programme_key,
    source,
    channel,
    schedule_date,
    programme_position,
    schedule_title,
    starts_at_local,
    programme_title,
    original_title,
    release_year,
    imdb_id,
    genres_json,
    metric_observation_id,
    popularity,
    vote_average,
    vote_count,
    metrics_observed_at,
    quality_score,
    confidence_score,
    popularity_score,
    highlight_score,
    row_number() over (
        partition by source, channel, schedule_date
        order by
            highlight_score desc,
            quality_score desc,
            confidence_score desc,
            starts_at_local,
            observation_id
    ) as highlight_rank,
    'v1' as ranking_version,
    '70% vote average, 20% log-scaled vote confidence, 10% log-scaled popularity'
        as ranking_explanation
from scored
