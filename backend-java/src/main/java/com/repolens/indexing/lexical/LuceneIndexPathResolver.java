package com.repolens.indexing.lexical;

import com.repolens.config.RepoLensProperties;
import org.springframework.stereotype.Component;

import java.nio.file.Path;

@Component
public class LuceneIndexPathResolver {

    private final RepoLensProperties properties;

    public LuceneIndexPathResolver(RepoLensProperties properties) {
        this.properties = properties;
    }

    public Path resolveRepositoryIndexPath(String repositoryId) {
        if (repositoryId == null || repositoryId.isBlank()) {
            throw new IllegalArgumentException("Repository id must not be blank");
        }
        Path indexRoot = Path.of(properties.getIndexRoot()).toAbsolutePath().normalize();
        Path repositoryPath = indexRoot.resolve("lucene").resolve(repositoryId).normalize();
        if (!repositoryPath.startsWith(indexRoot)) {
            throw new IllegalArgumentException("Invalid repository id for index path");
        }
        return repositoryPath;
    }
}
