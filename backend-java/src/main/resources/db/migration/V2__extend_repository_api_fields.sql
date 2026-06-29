alter table repositories
    add column commit_hash varchar(255);

alter table repositories
    add column parsed_file_count integer not null default 0;

alter table repositories
    add column relation_count integer not null default 0;
