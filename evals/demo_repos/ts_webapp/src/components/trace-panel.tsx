type Trace = {
  id: string;
  agentName: string;
  message: string;
};


type Props = {
  traces: Trace[];
};


export function TracePanel({ traces }: Props) {
  return (
    <section>
      <h2>Trace</h2>
      {traces.map((trace) => (
        <article key={trace.id}>
          <strong>{trace.agentName}</strong>
          <p>{trace.message}</p>
        </article>
      ))}
    </section>
  );
}
