import { EvaluationPanel } from "@/components/evaluation-panel";
import { EvidencePanel } from "@/components/evidence-panel";
import { RepositoryList } from "@/components/repository-list";
import { ReviewPanel } from "@/components/review-panel";
import { TracePanel } from "@/components/trace-panel";
import { fetchRepositories } from "@/lib/repositories";


export default async function DashboardPage() {
  const repositories = await fetchRepositories();

  return (
    <main>
      <h1>RepoLens Dashboard</h1>
      <RepositoryList repositories={repositories} />
      <EvaluationPanel />
      <ReviewPanel />
      <EvidencePanel evidences={[]} />
      <TracePanel traces={[]} />
    </main>
  );
}
