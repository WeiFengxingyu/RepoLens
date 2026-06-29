create table index_tasks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    status varchar(64) not null,
    current_stage varchar(64) not null,
    progress_percent integer not null default 0,
    last_error text,
    started_at timestamp,
    finished_at timestamp,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_index_tasks_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_index_tasks_repo on index_tasks(repository_id, created_at);
create index idx_index_tasks_status on index_tasks(status);

create table index_task_events (
    id varchar(64) primary key,
    task_id varchar(64) not null,
    repository_id varchar(64) not null,
    stage varchar(64) not null,
    status varchar(32) not null,
    message text,
    file_count integer not null default 0,
    parsed_file_count integer not null default 0,
    chunk_count integer not null default 0,
    symbol_count integer not null default 0,
    relation_count integer not null default 0,
    created_at timestamp not null,
    constraint fk_index_task_events_task
        foreign key (task_id) references index_tasks(id)
        on delete cascade,
    constraint fk_index_task_events_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_index_task_events_task on index_task_events(task_id, created_at);
create index idx_index_task_events_repo on index_task_events(repository_id, created_at);
