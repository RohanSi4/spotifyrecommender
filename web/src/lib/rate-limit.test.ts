import { describe, expect, it } from "vitest";

import { allowRequest, requestIdentity } from "./rate-limit";

describe("API rate limiting", () => {
  it("allows requests until the bucket limit is reached", () => {
    const key = `test-${crypto.randomUUID()}`;
    expect(allowRequest(key, 2)).toBe(true);
    expect(allowRequest(key, 2)).toBe(true);
    expect(allowRequest(key, 2)).toBe(false);
  });

  it("uses the first forwarded address as the request identity", () => {
    const headers = new Headers({ "x-forwarded-for": "203.0.113.5, 10.0.0.2" });
    expect(requestIdentity(headers)).toBe("203.0.113.5");
  });
});
