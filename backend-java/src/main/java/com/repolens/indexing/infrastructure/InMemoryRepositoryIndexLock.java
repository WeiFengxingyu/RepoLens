package com.repolens.indexing.infrastructure;

import com.repolens.indexing.application.RepositoryIndexLock;
import org.springframework.stereotype.Component;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class InMemoryRepositoryIndexLock implements RepositoryIndexLock {

    private final Set<String> activeRepositoryIds = ConcurrentHashMap.newKeySet();

    @Override
    public boolean tryLock(String repositoryId) {
        return activeRepositoryIds.add(repositoryId);
    }

    @Override
    public void unlock(String repositoryId) {
        activeRepositoryIds.remove(repositoryId);
    }
}
