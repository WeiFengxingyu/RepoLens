create table evaluation_runs (
    id varchar(64) primary key,
    name varchar(256) not null,
    dataset_path varchar(1024) not null,
    strategy varchar(64) not null,
    status varchar(32) not null,
    sample_count integer not null,
    repository_map text not null,
    metrics text,
    warnings text,
    error_message text,
    created_at timestamp not null,
    started_at timestamp,
    completed_at timestamp
);

create index idx_evaluation_runs_created_at on evaluation_runs(created_at);
create index idx_evaluation_runs_status on evaluation_runs(status);

create table evaluation_results (
    id varchar(64) primary key,
    run_id varchar(64) not null,
    sample_id varchar(128) not null,
    sample_type varchar(64) not null,
    repository_key varchar(128) not null,
    strategy varchar(64) not null,
    hit_at_5 boolean not null,
    mrr double precision not null,
    citation_coverage double precision not null,
    latency_ms bigint not null,
    token_count integer not null,
    token_estimated boolean not null,
    matched_files text,
    matched_symbols text,
    citations text,
    error_message text,
    created_at timestamp not null,
    constraint fk_evaluation_results_run
        foreign key (run_id) references evaluation_runs(id)
        on delete cascade
);

create index idx_evaluation_results_run on evaluation_results(run_id, strategy, sample_id);
create index idx_evaluation_results_sample on evaluation_results(sample_id);
