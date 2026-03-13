import { describe, expect, it } from "vitest";
import { api } from "./client";

describe("api client", () => {
  it("is an openapi-fetch client instance", () => {
    expect(api).toBeDefined();
    expect(api.GET).toBeTypeOf("function");
  });
});
