create table review_tasks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    status varchar(32) not null,
    diff_text text not null,
    summary text,
    risk_level varchar(32),
    risks text,
    impacted_symbols text,
    suggested_tests text,
    citations text,
    markdown text,
    error_message text,
    created_at timestamp not null,
    completed_at timestamp,
    constraint fk_review_tasks_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_review_tasks_repository on review_tasks(repository_id, created_at);
create index idx_review_tasks_status on review_tasks(status);

create table review_tool_calls (
    id varchar(64) primary key,
    task_id varchar(64) not null,
    repository_id varchar(64) not null,
    tool_name varchar(128) not null,
    status varchar(32) not null,
    permission_decision varchar(32) not null,
    input_summary text,
    output_summary text,
    latency_ms bigint,
    error_message text,
    created_at timestamp not null,
    completed_at timestamp,
    constraint fk_review_tool_calls_task
        foreign key (task_id) references review_tasks(id)
        on delete cascade,
    constraint fk_review_tool_calls_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_review_tool_calls_task on review_tool_calls(task_id, created_at);
