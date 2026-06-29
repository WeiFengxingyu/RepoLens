package com.repolens.retrieval.application;

import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;

@Component
public class EvidenceIdFactory {

    public String create(String repositoryId, String chunkId, String source, int rank) {
        String value = repositoryId + ":" + chunkId + ":" + source + ":" + rank;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(value.getBytes(StandardCharsets.UTF_8));
            return "ev_" + HexFormat.of().formatHex(hash).substring(0, 24);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is not available", exception);
        }
    }
}
