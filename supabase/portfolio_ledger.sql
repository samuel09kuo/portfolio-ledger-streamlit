create table if not exists public.portfolio_ledger (
    trade_id text primary key,
    trade_date date not null,
    symbol text not null,
    market text not null,
    name text not null default '',
    action text not null,
    shares double precision not null default 0,
    price double precision not null default 0,
    fee double precision not null default 0,
    tax double precision not null default 0,
    currency text not null default '',
    order_id text not null default '',
    broker text not null default '',
    account text not null default '',
    source text not null default '',
    note text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists portfolio_ledger_trade_date_idx
    on public.portfolio_ledger (trade_date desc, created_at desc);

alter table public.portfolio_ledger enable row level security;

drop policy if exists "portfolio_ledger_read_write" on public.portfolio_ledger;
create policy "portfolio_ledger_read_write"
on public.portfolio_ledger
for all
to anon, authenticated
using (true)
with check (true);
