package com.repolens.indexing.lexical;

import com.repolens.chunking.domain.CodeChunkEntity;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexNotFoundException;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.queryparser.classic.MultiFieldQueryParser;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class LuceneIndexService {

    private static final String[] QUERY_FIELDS = {
            LuceneDocumentMapper.FIELD_SYMBOL_NAME,
            LuceneDocumentMapper.FIELD_FILE_PATH,
            LuceneDocumentMapper.FIELD_METADATA,
            LuceneDocumentMapper.FIELD_CONTENT
    };

    private static final Map<String, Float> FIELD_BOOSTS = Map.of(
            LuceneDocumentMapper.FIELD_SYMBOL_NAME, 4.0F,
            LuceneDocumentMapper.FIELD_FILE_PATH, 2.5F,
            LuceneDocumentMapper.FIELD_METADATA, 2.0F,
            LuceneDocumentMapper.FIELD_CONTENT, 1.0F
    );

    private final LuceneIndexPathResolver pathResolver;
    private final LuceneDocumentMapper documentMapper;

    public LuceneIndexService(LuceneIndexPathResolver pathResolver, LuceneDocumentMapper documentMapper) {
        this.pathResolver = pathResolver;
        this.documentMapper = documentMapper;
    }

    public void rebuildIndex(String repositoryId, List<CodeChunkEntity> chunks) {
        Path indexPath = pathResolver.resolveRepositoryIndexPath(repositoryId);
        try {
            Files.createDirectories(indexPath);
            try (Analyzer analyzer = new StandardAnalyzer();
                 Directory directory = FSDirectory.open(indexPath)) {
                IndexWriterConfig config = new IndexWriterConfig(analyzer);
                config.setOpenMode(IndexWriterConfig.OpenMode.CREATE);
                try (IndexWriter writer = new IndexWriter(directory, config)) {
                    for (CodeChunkEntity chunk : chunks) {
                        writer.addDocument(documentMapper.toDocument(chunk));
                    }
                    writer.commit();
                }
            }
        } catch (IOException exception) {
            throw new LuceneIndexException("Failed to rebuild Lucene index", exception);
        }
    }

    public List<LexicalSearchHit> search(String repositoryId, String queryText, int topK) {
        if (queryText == null || queryText.isBlank() || topK <= 0) {
            return List.of();
        }

        Path indexPath = pathResolver.resolveRepositoryIndexPath(repositoryId);
        if (!Files.exists(indexPath)) {
            return List.of();
        }

        try (Analyzer analyzer = new StandardAnalyzer();
             Directory directory = FSDirectory.open(indexPath);
             DirectoryReader reader = DirectoryReader.open(directory)) {
            IndexSearcher searcher = new IndexSearcher(reader);
            Query query = parseQuery(analyzer, queryText);
            TopDocs topDocs = searcher.search(query, topK);
            List<LexicalSearchHit> hits = new ArrayList<>();
            int rank = 1;
            for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
                String chunkId = searcher.storedFields()
                        .document(scoreDoc.doc)
                        .get(LuceneDocumentMapper.FIELD_CHUNK_ID);
                if (chunkId != null && !chunkId.isBlank()) {
                    hits.add(new LexicalSearchHit(chunkId, scoreDoc.score, rank));
                    rank++;
                }
            }
            return hits;
        } catch (IndexNotFoundException exception) {
            return List.of();
        } catch (IOException | ParseException exception) {
            throw new LuceneIndexException("Failed to search Lucene index", exception);
        }
    }

    private Query parseQuery(Analyzer analyzer, String queryText) throws ParseException {
        MultiFieldQueryParser parser = new MultiFieldQueryParser(QUERY_FIELDS, analyzer, FIELD_BOOSTS);
        parser.setDefaultOperator(QueryParser.Operator.OR);
        return parser.parse(QueryParser.escape(queryText.trim()));
    }
}
