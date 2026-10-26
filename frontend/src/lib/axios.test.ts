import { AxiosError, AxiosHeaders } from "axios";
import { describe, expect, it } from "vitest";

import { toApiError } from "@/lib/axios";

/**
 * toApiError is the one place every backend error response gets
 * normalized before reaching the UI (see lib/axios.ts) - these tests
 * lock in the exact backend error shapes documented in
 * docs/api/rest_api.md: {"detail": "..."} for most errors,
 * {"detail": [{loc, msg}, ...]} for 422 validation errors, and no
 * response at all for a genuine network failure.
 */
function axiosErrorWithResponse(status: number, data: unknown): AxiosError {
  const error = new AxiosError("Request failed", String(status));
  error.response = {
    status,
    data,
    statusText: "",
    headers: {},
    config: { headers: new AxiosHeaders() },
  };
  return error;
}

describe("toApiError", () => {
  it("passes through a real string detail message", () => {
    const error = axiosErrorWithResponse(404, { detail: "Video not found" });
    const result = toApiError(error);
    expect(result.status).toBe(404);
    expect(result.message).toBe("Video not found");
    expect(result.fieldErrors).toBeNull();
  });

  it("extracts field errors from a 422 validation response", () => {
    const error = axiosErrorWithResponse(422, {
      detail: [
        { loc: ["body", "email"], msg: "value is not a valid email address" },
        { loc: ["body", "password"], msg: "field required" },
      ],
    });
    const result = toApiError(error);
    expect(result.status).toBe(422);
    expect(result.fieldErrors).toEqual([
      { field: "email", message: "value is not a valid email address" },
      { field: "password", message: "field required" },
    ]);
    expect(result.message).toBe("value is not a valid email address");
  });

  it("falls back to a status-appropriate message when detail is missing", () => {
    const error = axiosErrorWithResponse(500, {});
    const result = toApiError(error);
    expect(result.status).toBe(500);
    expect(result.message).toMatch(/server ran into a problem/i);
  });

  it("reports a distinct message for a genuine network failure (no response at all)", () => {
    const error = new AxiosError("Network Error");
    // No .response set - this is exactly what a DNS/connection failure
    // looks like to axios, as opposed to a real HTTP error status.
    const result = toApiError(error);
    expect(result.status).toBeNull();
    expect(result.message).toMatch(/can't reach the server/i);
  });

  it("never leaks a raw, unrecognized error object as the message", () => {
    const result = toApiError(new Error("some internal JS error"));
    expect(result.message).not.toContain("some internal JS error");
  });
});
