create table organizations (
    id varchar(64) primary key,
    name varchar(256) not null,
    plan_name varchar(64) not null,
    status varchar(64) not null,
    created_at timestamp not null,
    updated_at timestamp not null
);

create index idx_organizations_created_at on organizations(created_at);

create table projects (
    id varchar(64) primary key,
    organization_id varchar(64) not null,
    name varchar(256) not null,
    status varchar(64) not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_projects_organization
        foreign key (organization_id) references organizations(id)
        on delete cascade
);

create index idx_projects_organization on projects(organization_id, created_at);

create table team_members (
    id varchar(64) primary key,
    organization_id varchar(64) not null,
    user_id varchar(128) not null,
    role_name varchar(64) not null,
    created_at timestamp not null,
    constraint fk_team_members_organization
        foreign key (organization_id) references organizations(id)
        on delete cascade
);

create unique index ux_team_members_org_user on team_members(organization_id, user_id);

create table repository_bindings (
    id varchar(64) primary key,
    project_id varchar(64) not null,
    repository_id varchar(64) not null,
    provider varchar(64) not null,
    external_repo_id varchar(512) not null,
    webhook_secret_hash varchar(128),
    enabled boolean not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_repository_bindings_project
        foreign key (project_id) references projects(id)
        on delete cascade,
    constraint fk_repository_bindings_repository
        foreign key (repository_id) references repositories(id)
        on delete cascade
);

create unique index ux_repository_bindings_provider_external on repository_bindings(provider, external_repo_id);
create unique index ux_repository_bindings_project_repository on repository_bindings(project_id, repository_id);
create index idx_repository_bindings_project on repository_bindings(project_id, created_at);

create table review_rulesets (
    id varchar(64) primary key,
    project_id varchar(64) not null,
    name varchar(256) not null,
    rules_json text not null,
    enabled boolean not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    constraint fk_review_rulesets_project
        foreign key (project_id) references projects(id)
        on delete cascade
);

create index idx_review_rulesets_project on review_rulesets(project_id, created_at);
create index idx_review_rulesets_project_enabled on review_rulesets(project_id, enabled, created_at);

create table quota_buckets (
    id varchar(64) primary key,
    scope_type varchar(64) not null,
    scope_id varchar(64) not null,
    quota_type varchar(64) not null,
    used_count integer not null,
    limit_count integer not null,
    window_start timestamp not null,
    window_end timestamp not null,
    created_at timestamp not null,
    updated_at timestamp not null
);

create unique index ux_quota_buckets_window on quota_buckets(scope_type, scope_id, quota_type, window_start);
create index idx_quota_buckets_scope on quota_buckets(scope_type, scope_id, quota_type, window_end);

create table audit_logs (
    id varchar(64) primary key,
    actor varchar(128),
    action varchar(128) not null,
    scope_type varchar(64) not null,
    scope_id varchar(64) not null,
    message text,
    payload_json text,
    created_at timestamp not null
);

create index idx_audit_logs_created_at on audit_logs(created_at);
create index idx_audit_logs_scope on audit_logs(scope_type, scope_id, created_at);
