import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, ApiError } from "../src/api/client";

describe("API Client Envelope & Error Handling", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("unwraps { data: ..., meta: ... } envelope on successful response", async () => {
    const mockData = { id: "user_123", email: "analyst@brand.in" };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({
        data: mockData,
        meta: { request_id: "req_test_123", generated_at: "2026-11-14T00:00:00Z" },
      }),
    });

    const result = await apiClient.get<typeof mockData>("/me");
    expect(result).toEqual(mockData);
  });

  it("parses structured { error: { code, message, details, request_id } } on 4xx/5xx responses", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      headers: new Headers({ "content-type": "application/json" }),
      json: async () => ({
        error: {
          code: "TENANT_ACCESS_DENIED",
          message: "Resource does not belong to active workspace.",
          details: { workspace_id: "ws_456" },
          request_id: "req_err_789",
        },
      }),
    });

    try {
      await apiClient.get("/dashboard/summary");
      expect.fail("Should have thrown ApiError");
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(403);
      expect(apiErr.code).toBe("TENANT_ACCESS_DENIED");
      expect(apiErr.message).toBe("Resource does not belong to active workspace.");
      expect(apiErr.requestId).toBe("req_err_789");
      expect(apiErr.details).toEqual({ workspace_id: "ws_456" });
    }
  });

  it("throws fallback ApiError when non-JSON error is returned", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      headers: new Headers({ "content-type": "text/html" }),
      json: async () => {
        throw new Error("Not JSON");
      },
    });

    await expect(apiClient.get("/sources")).rejects.toThrow("HTTP error 502: Bad Gateway");
  });
});
