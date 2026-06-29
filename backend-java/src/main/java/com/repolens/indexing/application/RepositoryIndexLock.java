package com.repolens.indexing.application;

public interface RepositoryIndexLock {

    boolean tryLock(String repositoryId);

    void unlock(String repositoryId);
}
