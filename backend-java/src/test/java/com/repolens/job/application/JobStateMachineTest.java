package com.repolens.job.application;

import com.repolens.job.domain.JobStatus;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JobStateMachineTest {

    private final JobStateMachine stateMachine = new JobStateMachine();

    @Test
    void allowsExpectedHappyPathTransitions() {
        assertThatCode(() -> {
            stateMachine.validate(JobStatus.CREATED, JobStatus.QUEUED);
            stateMachine.validate(JobStatus.QUEUED, JobStatus.RUNNING);
            stateMachine.validate(JobStatus.RUNNING, JobStatus.SUCCEEDED);
        }).doesNotThrowAnyException();
    }

    @Test
    void rejectsIllegalTransitionFromTerminalStatus() {
        assertThatThrownBy(() -> stateMachine.validate(JobStatus.SUCCEEDED, JobStatus.RUNNING))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Illegal job status transition");
    }
}
