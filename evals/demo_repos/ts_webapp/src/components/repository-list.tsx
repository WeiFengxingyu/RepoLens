type Repository = {
  id: string;
  name: string;
  status: string;
};


type Props = {
  repositories: Repository[];
};


export function RepositoryList({ repositories }: Props) {
  return (
    <section>
      <h2>Repositories</h2>
      <ul>
        {repositories.map((repository) => (
          <li key={repository.id}>
            <button type="button">{repository.name}</button>
            <span>{repository.status}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
