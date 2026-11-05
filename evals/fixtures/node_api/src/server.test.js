import { describe, expect, it } from "vitest";

import { app } from "./server.js";

describe("health", () => {
  it("has an express app", () => {
    expect(app).toBeDefined();
  });
});
