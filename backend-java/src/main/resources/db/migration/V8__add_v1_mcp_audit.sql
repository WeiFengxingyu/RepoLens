create table mcp_tool_call_audits (
    id varchar(64) primary key,
    task_id varchar(64) not null,
    repository_id varchar(64),
    tool_name varchar(128) not null,
    status varchar(32) not null,
    permission_decision varchar(32) not null,
    permission_policy varchar(128),
    client_name varchar(128),
    client_session_id varchar(128),
    input_hash varchar(128),
    output_hash varchar(128),
    input_summary text,
    output_summary text,
    latency_ms bigint,
    error_message text,
    created_at timestamp not null,
    completed_at timestamp,
    constraint fk_mcp_tool_call_audits_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_mcp_tool_call_audits_created_at on mcp_tool_call_audits(created_at);
create index idx_mcp_tool_call_audits_repository on mcp_tool_call_audits(repository_id, created_at);
create index idx_mcp_tool_call_audits_tool on mcp_tool_call_audits(tool_name, created_at);
