type Evidence = {
  id: string;
  filePath: string;
  snippet: string;
  score: number;
  source: string;
};


type Props = {
  evidences: Evidence[];
};


export function EvidencePanel({ evidences }: Props) {
  return (
    <section>
      <h2>Evidence</h2>
      <ul>
        {evidences.map((evidence) => (
          <li key={evidence.id}>
            <strong>{evidence.filePath}</strong>
            <span>{evidence.score.toFixed(3)}</span>
            <p>{evidence.snippet}</p>
            <small>{evidence.source}</small>
          </li>
        ))}
      </ul>
    </section>
  );
}
