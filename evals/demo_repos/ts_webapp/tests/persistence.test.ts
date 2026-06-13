import { restoreWorkspaceState } from "../src/lib/persistence";


it("falls back when persisted workspace state is invalid", () => {
  expect(restoreWorkspaceState("{")).toEqual({
    selectedRepositoryId: null,
    activePanel: "repositories",
  });
});
