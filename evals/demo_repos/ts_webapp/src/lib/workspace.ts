export type WorkspaceTab = "repositories" | "ask" | "review" | "evaluation";


export function selectInitialTab(hasRepository: boolean): WorkspaceTab {
  return hasRepository ? "ask" : "repositories";
}
