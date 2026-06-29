create table vector_chunks (
    id varchar(64) primary key,
    repository_id varchar(64) not null,
    chunk_id varchar(64) not null,
    embedding_model varchar(128) not null,
    dimensions integer not null,
    embedding text not null,
    content_hash varchar(128),
    created_at timestamp not null,
    constraint fk_vector_chunks_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade,
    constraint fk_vector_chunks_chunk
        foreign key (chunk_id) references code_chunks(id)
        on delete cascade
);

create unique index idx_vector_chunks_chunk on vector_chunks(repository_id, chunk_id);
create index idx_vector_chunks_repo on vector_chunks(repository_id);
