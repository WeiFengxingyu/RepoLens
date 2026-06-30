create table analysis_jobs (
    id varchar(64) primary key,
    job_type varchar(64) not null,
    status varchar(64) not null,
    priority integer not null default 5,
    repository_id varchar(64),
    project_id varchar(64),
    idempotency_key varchar(256),
    payload_json text,
    result_ref varchar(256),
    created_by varchar(128),
    next_run_at timestamp,
    started_at timestamp,
    finished_at timestamp,
    last_error_code varchar(128),
    last_error_message text,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_analysis_jobs_repository
        foreign key (repository_id) references repositories(id)
        on delete set null
);

create unique index ux_analysis_jobs_idempotency_key on analysis_jobs(idempotency_key);
create index idx_analysis_jobs_status on analysis_jobs(status, created_at);
create index idx_analysis_jobs_type_status on analysis_jobs(job_type, status);
create index idx_analysis_jobs_repository on analysis_jobs(repository_id, created_at);

create table job_attempts (
    id varchar(64) primary key,
    job_id varchar(64) not null,
    attempt_no integer not null,
    worker_id varchar(128) not null,
    status varchar(64) not null,
    started_at timestamp not null,
    heartbeat_at timestamp,
    finished_at timestamp,
    error_code varchar(128),
    error_message text,
    constraint fk_job_attempts_job
        foreign key (job_id) references analysis_jobs(id)
        on delete cascade
);

create unique index ux_job_attempts_job_attempt_no on job_attempts(job_id, attempt_no);
create index idx_job_attempts_job on job_attempts(job_id, started_at);
create index idx_job_attempts_worker on job_attempts(worker_id, heartbeat_at);

create table job_events (
    id varchar(64) primary key,
    job_id varchar(64) not null,
    attempt_id varchar(64),
    event_type varchar(64) not null,
    message text,
    payload_json text,
    created_at timestamp not null,
    constraint fk_job_events_job
        foreign key (job_id) references analysis_jobs(id)
        on delete cascade,
    constraint fk_job_events_attempt
        foreign key (attempt_id) references job_attempts(id)
        on delete set null
);

create index idx_job_events_job on job_events(job_id, created_at);

create table dead_letter_jobs (
    job_id varchar(64) primary key,
    reason varchar(128) not null,
    final_error text,
    attempt_count integer not null,
    payload_json text,
    created_at timestamp not null,
    constraint fk_dead_letter_jobs_job
        foreign key (job_id) references analysis_jobs(id)
        on delete cascade
);
