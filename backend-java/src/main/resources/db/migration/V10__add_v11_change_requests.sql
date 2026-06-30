create table change_requests (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    review_task_id varchar(64),
    platform varchar(32) not null,
    change_type varchar(32) not null,
    owner_name varchar(512) not null,
    repository_name varchar(256) not null,
    change_number varchar(64) not null,
    url varchar(2048) not null,
    title text not null,
    author varchar(256),
    source_branch varchar(512),
    target_branch varchar(512),
    state varchar(64),
    changed_file_count integer not null,
    addition_count integer not null,
    deletion_count integer not null,
    commit_count integer not null,
    provider_status varchar(32) not null,
    metadata_json text,
    diff_hash varchar(128),
    error_message text,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_change_requests_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade,
    constraint fk_change_requests_review_task
        foreign key (review_task_id) references review_tasks(id)
        on delete set null
);

create index idx_change_requests_repository on change_requests(repository_id, created_at);
create index idx_change_requests_review_task on change_requests(review_task_id);
create index idx_change_requests_platform on change_requests(platform, owner_name, repository_name, change_number);
