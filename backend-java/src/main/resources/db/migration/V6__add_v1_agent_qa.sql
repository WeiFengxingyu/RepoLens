create table qa_tasks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    status varchar(32) not null,
    question text not null,
    answer text,
    confidence double precision,
    warnings text,
    error_message text,
    created_at timestamp not null,
    completed_at timestamp,
    constraint fk_qa_tasks_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_qa_tasks_repository on qa_tasks(repository_id, created_at);
create index idx_qa_tasks_status on qa_tasks(status);

create table agent_traces (
    id varchar(64) primary key,
    task_id varchar(64) not null,
    repository_id varchar(64) not null,
    step_name varchar(128) not null,
    step_order integer not null,
    status varchar(32) not null,
    input_summary text,
    output_summary text,
    evidence_ids text,
    tool_calls text,
    token_usage text,
    latency_ms bigint,
    error_message text,
    created_at timestamp not null,
    completed_at timestamp
);

create index idx_agent_traces_task on agent_traces(task_id, step_order);
create index idx_agent_traces_repository on agent_traces(repository_id, created_at);
