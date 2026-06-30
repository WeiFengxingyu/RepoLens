package com.repolens.change.application;

public interface ChangeRequestProvider {
    boolean supports(ChangeRequestRef ref);

    FetchedChangeRequest fetch(ChangeRequestRef ref);
}
