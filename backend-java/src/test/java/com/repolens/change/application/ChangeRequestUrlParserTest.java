package com.repolens.change.application;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ChangeRequestUrlParserTest {

    private final ChangeRequestUrlParser parser = new ChangeRequestUrlParser();

    @Test
    void parsesSupportedPlatformUrls() {
        ChangeRequestRef github = parser.parse("https://github.com/acme/service/pull/42");
        assertThat(github.platform()).isEqualTo("github");
        assertThat(github.owner()).isEqualTo("acme");
        assertThat(github.repo()).isEqualTo("service");
        assertThat(github.number()).isEqualTo("42");

        ChangeRequestRef gitee = parser.parse("https://gitee.com/acme/service/pulls/7");
        assertThat(gitee.platform()).isEqualTo("gitee");
        assertThat(gitee.changeType()).isEqualTo("pull_request");

        ChangeRequestRef gitlab = parser.parse("https://gitlab.com/group/sub/service/-/merge_requests/9");
        assertThat(gitlab.platform()).isEqualTo("gitlab");
        assertThat(gitlab.owner()).isEqualTo("group/sub");
        assertThat(gitlab.repo()).isEqualTo("service");
        assertThat(gitlab.changeType()).isEqualTo("merge_request");
    }

    @Test
    void parsesFixtureUrls() {
        ChangeRequestRef fixture = parser.parse("fixture://github/repolens-java/1");

        assertThat(fixture.platform()).isEqualTo("fixture-github");
        assertThat(fixture.owner()).isEqualTo("fixture");
        assertThat(fixture.repo()).isEqualTo("repolens-java");
        assertThat(fixture.number()).isEqualTo("1");
    }
}
