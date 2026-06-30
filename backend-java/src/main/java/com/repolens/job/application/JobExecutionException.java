package com.repolens.job.application;

public class JobExecutionException extends RuntimeException {

    private final String errorCode;
    private final boolean retryable;

    public JobExecutionException(String errorCode, String message, boolean retryable) {
        super(message);
        this.errorCode = errorCode;
        this.retryable = retryable;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public boolean isRetryable() {
        return retryable;
    }
}
