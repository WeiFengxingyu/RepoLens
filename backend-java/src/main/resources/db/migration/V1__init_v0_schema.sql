create table repositories (
    id varchar(64) primary key,
    name varchar(255) not null,
    source_type varchar(32) not null,
    source_url varchar(1024),
    local_path varchar(1024),
    branch_name varchar(255),
    status varchar(64) not null,
    file_count integer not null default 0,
    chunk_count integer not null default 0,
    skipped_file_count integer not null default 0,
    language_summary text,
    last_error text,
    created_at timestamp not null,
    updated_at timestamp not null,
    indexed_at timestamp
);

create table repository_files (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    relative_path varchar(1024) not null,
    language varchar(64) not null,
    size_bytes bigint not null,
    content_hash varchar(128),
    skipped boolean not null default false,
    skip_reason varchar(255),
    created_at timestamp not null,
    constraint fk_repository_files_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_repository_files_repo on repository_files(repository_id);
create index idx_repository_files_path on repository_files(repository_id, relative_path);

create table code_chunks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    file_id varchar(64) not null,
    file_path varchar(1024) not null,
    language varchar(64) not null,
    symbol_name varchar(512),
    symbol_type varchar(64) not null,
    start_line integer not null,
    end_line integer not null,
    content_hash varchar(128),
    content text not null,
    token_estimate integer not null default 0,
    metadata text,
    created_at timestamp not null,
    constraint fk_code_chunks_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade,
    constraint fk_code_chunks_file
        foreign key (file_id) references repository_files(id)
        on delete cascade
);

create index idx_code_chunks_repo on code_chunks(repository_id);
create index idx_code_chunks_file on code_chunks(repository_id, file_path);
create index idx_code_chunks_symbol on code_chunks(repository_id, symbol_name);
