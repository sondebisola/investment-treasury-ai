with source as (
    select * from {{ source('raw_treasury', 'raw_trade_executions') }}
),

renamed as (
    select
        cast(trade_id as string) as trade_id,
        upper(asset_class) as asset_class,
        upper(ticker) as ticker,
        cast(counterparty_id as string) as counterparty_id,
        cast(notional_amount as numeric) as notional_amount,
        cast(yield_pct as numeric) as yield_pct,
        timestamp(execution_timestamp) as execution_timestamp,
        upper(liquidity_tier) as liquidity_tier
    from source
)

select * from renamed
