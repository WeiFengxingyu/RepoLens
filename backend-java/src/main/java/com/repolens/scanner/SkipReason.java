package com.repolens.scanner;

public enum SkipReason {
    IGNORED_DIRECTORY,
    SYMLINK_DIRECTORY,
    SYMLINK_FILE,
    IGNORED_FILE,
    FILE_TOO_LARGE,
    BINARY_FILE,
    STAT_FAILED,
    READ_FAILED,
    PATH_ESCAPES_ROOT
}
