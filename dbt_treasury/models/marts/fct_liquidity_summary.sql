with trades as (
    select * from {{ ref('stg_trade_executions') }}
)

select
    asset_class,
    liquidity_tier,
    count(trade_id) as total_trades,
    sum(notional_amount) as total_notional_exposure,
    round(avg(yield_pct), 4) as avg_yield_pct,
    min(execution_timestamp) as first_trade_at,
    max(execution_timestamp) as last_trade_at
from trades
group by 1, 2
