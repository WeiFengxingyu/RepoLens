package com.repolens.indexing.lexical;

import com.repolens.chunking.domain.CodeChunkEntity;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StoredField;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.springframework.stereotype.Component;

@Component
public class LuceneDocumentMapper {

    public static final String FIELD_CHUNK_ID = "chunk_id";
    public static final String FIELD_REPOSITORY_ID = "repository_id";
    public static final String FIELD_FILE_PATH = "file_path";
    public static final String FIELD_LANGUAGE = "language";
    public static final String FIELD_SYMBOL_NAME = "symbol_name";
    public static final String FIELD_SYMBOL_TYPE = "symbol_type";
    public static final String FIELD_CONTENT = "content";
    public static final String FIELD_METADATA = "metadata";

    public Document toDocument(CodeChunkEntity chunk) {
        Document document = new Document();
        document.add(new StoredField(FIELD_CHUNK_ID, chunk.getId()));
        document.add(new StringField(FIELD_REPOSITORY_ID, safe(chunk.getRepositoryId()), Field.Store.YES));
        document.add(new TextField(FIELD_FILE_PATH, safe(chunk.getFilePath()), Field.Store.YES));
        document.add(new StringField(FIELD_LANGUAGE, safe(chunk.getLanguage()), Field.Store.YES));
        document.add(new TextField(FIELD_SYMBOL_NAME, safe(chunk.getSymbolName()), Field.Store.YES));
        document.add(new StringField(FIELD_SYMBOL_TYPE, chunk.getSymbolType().name(), Field.Store.YES));
        document.add(new TextField(FIELD_CONTENT, safe(chunk.getContent()), Field.Store.YES));
        document.add(new TextField(FIELD_METADATA, safe(chunk.getMetadata()), Field.Store.YES));
        return document;
    }

    private String safe(String value) {
        return value == null ? "" : value;
    }
}
