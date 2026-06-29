create table code_symbols (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    file_path varchar(1024) not null,
    language varchar(64) not null,
    symbol_name varchar(512) not null,
    qualified_name varchar(1024) not null,
    symbol_type varchar(64) not null,
    parent_symbol_name varchar(1024),
    start_line integer not null,
    end_line integer not null,
    signature text,
    metadata text,
    created_at timestamp not null,
    constraint fk_code_symbols_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_code_symbols_repo on code_symbols(repository_id);
create index idx_code_symbols_name on code_symbols(repository_id, symbol_name);
create index idx_code_symbols_qualified on code_symbols(repository_id, qualified_name);
create index idx_code_symbols_file on code_symbols(repository_id, file_path);

create table code_relations (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    relation_type varchar(64) not null,
    source_symbol_id varchar(64),
    target_symbol_id varchar(64),
    source_name varchar(1024),
    target_name varchar(1024),
    file_path varchar(1024),
    metadata text,
    created_at timestamp not null,
    constraint fk_code_relations_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create index idx_code_relations_repo on code_relations(repository_id);
create index idx_code_relations_source on code_relations(repository_id, source_symbol_id);
create index idx_code_relations_target on code_relations(repository_id, target_symbol_id);
create index idx_code_relations_type on code_relations(repository_id, relation_type);
