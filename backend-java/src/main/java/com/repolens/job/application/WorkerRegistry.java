package com.repolens.job.application;

import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class WorkerRegistry {

    private final Clock clock;
    private final Map<String, WorkerSnapshot> workers = new ConcurrentHashMap<>();

    public WorkerRegistry(Clock clock) {
        this.clock = clock;
    }

    public void markRunning(String workerId, String jobId) {
        workers.put(workerId, new WorkerSnapshot(workerId, "RUNNING", jobId, Instant.now(clock)));
    }

    public void markIdle(String workerId) {
        workers.put(workerId, new WorkerSnapshot(workerId, "IDLE", null, Instant.now(clock)));
    }

    public List<WorkerSnapshot> snapshots() {
        return workers.values().stream()
                .sorted(Comparator.comparing(WorkerSnapshot::workerId))
                .toList();
    }
}
