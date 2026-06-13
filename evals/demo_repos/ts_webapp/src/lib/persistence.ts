type WorkspaceState = {
  selectedRepositoryId: string | null;
  activePanel: string;
};


const defaultState: WorkspaceState = {
  selectedRepositoryId: null,
  activePanel: "repositories",
};


export function restoreWorkspaceState(raw: string | null): WorkspaceState {
  try {
    return raw ? JSON.parse(raw) : defaultState;
  } catch {
    return defaultState;
  }
}
