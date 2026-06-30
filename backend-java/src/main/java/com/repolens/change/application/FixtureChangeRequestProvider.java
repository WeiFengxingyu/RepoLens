package com.repolens.change.application;

import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class FixtureChangeRequestProvider implements ChangeRequestProvider {

    @Override
    public boolean supports(ChangeRequestRef ref) {
        return ref.platform().startsWith("fixture-");
    }

    @Override
    public FetchedChangeRequest fetch(ChangeRequestRef ref) {
        String path = "src/main/java/com/demo/SecurityConfig.java";
        String diff = """
                diff --git a/src/main/java/com/demo/SecurityConfig.java b/src/main/java/com/demo/SecurityConfig.java
                --- a/src/main/java/com/demo/SecurityConfig.java
                +++ b/src/main/java/com/demo/SecurityConfig.java
                @@ -2,6 +2,8 @@ package demo;
                 class SecurityConfig {
                   void configure() {
                -    requireAuth();
                +    permitAll();
                +    return null;
                   }
                 }
                """;
        return new FetchedChangeRequest(
                ref,
                "Fixture PR " + ref.number() + ": relax security config",
                "fixture-author",
                "feature/fixture-pr-" + ref.number(),
                "main",
                "opened",
                1,
                List.of(new ChangedRemoteFile(path, 2, 1)),
                diff,
                Map.of(
                        "fixture", true,
                        "provider", ref.platform(),
                        "note", "offline deterministic V1.1 fixture"
                ),
                List.of("fixture provider used; no network request was made")
        );
    }
}
