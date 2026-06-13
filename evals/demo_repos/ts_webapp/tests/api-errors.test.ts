import { readError } from "../src/lib/api-errors";


it("normalizes unknown errors", () => {
  expect(readError("boom")).toBe("Unexpected error");
});
