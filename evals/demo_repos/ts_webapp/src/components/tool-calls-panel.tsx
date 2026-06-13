type ToolCall = {
  id: string;
  toolName: string;
  permission: string;
  latencyMs: number;
};


type Props = {
  toolCalls: ToolCall[];
};


export function ToolCallsPanel({ toolCalls }: Props) {
  return (
    <section>
      <h2>Tool calls</h2>
      {toolCalls.map((toolCall) => (
        <article key={toolCall.id}>
          <strong>{toolCall.toolName}</strong>
          <span>{toolCall.permission}</span>
          <span>{toolCall.latencyMs} ms</span>
        </article>
      ))}
    </section>
  );
}
