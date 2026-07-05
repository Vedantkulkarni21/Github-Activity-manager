-- Reference schema. In practice the app creates these automatically on startup
-- (see app/database.py:init_models). Use this file if you'd rather run it
-- manually in the Supabase SQL editor.

create extension if not exists "pgcrypto";

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    github_id integer unique not null,
    username varchar not null,
    avatar_url varchar,
    access_token_encrypted text not null,
    created_at timestamptz default now()
);

create table if not exists repos (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    github_repo_id integer not null unique,
    owner_login varchar not null,
    name varchar not null,
    full_name varchar not null,
    webhook_id integer,
    is_active boolean default true,
    created_at timestamptz default now()
);
create index if not exists ix_repos_github_repo_id on repos(github_repo_id);

create table if not exists rules (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    repo_id uuid references repos(id) on delete cascade,
    event_type varchar not null,
    match_field varchar not null,
    match_type varchar default 'contains',
    match_value varchar not null,
    action_add_label varchar,
    action_comment_template text,
    action_slack_notify boolean default true,
    is_active boolean default true,
    created_at timestamptz default now()
);

create table if not exists events (
    id uuid primary key default gen_random_uuid(),
    repo_id uuid references repos(id) on delete cascade,
    delivery_id varchar not null unique,
    event_type varchar not null,
    action varchar,
    payload jsonb not null,
    status varchar default 'received',
    error_detail text,
    received_at timestamptz default now(),
    processed_at timestamptz
);
create index if not exists ix_events_delivery_id on events(delivery_id);

create table if not exists action_logs (
    id uuid primary key default gen_random_uuid(),
    event_id uuid references events(id) on delete cascade,
    rule_id uuid references rules(id) on delete set null,
    action_type varchar not null,
    status varchar not null,
    detail text,
    attempted_at timestamptz default now()
);
