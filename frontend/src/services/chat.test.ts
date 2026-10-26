import { afterEach, describe, expect, it, vi } from "vitest";

import { askVideoStream, STREAM_UNAVAILABLE } from "@/services/chat";

function sseResponse(body: string, init: ResponseInit = { status: 200 }): Response {
  return new Response(body, { ...init, headers: { "Content-Type": "text/event-stream" } });
}

describe("askVideoStream", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("forwards sources and tokens and resolves with the final result", async () => {
    window.localStorage.setItem("aivip_access_token", "token-123");
    const fetchMock = vi.fn().mockResolvedValue(
      sseResponse(
        'event: sources\ndata: {"sources":[]}\n\n' +
          'event: token\ndata: {"text":"Xin "}\n\n' +
          'event: token\ndata: {"text":"chào"}\n\n' +
          'event: done\ndata: {"video_id":3,"query":"hi","status":"answered","answer":"Xin chào","sources":[]}\n\n',
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const onSources = vi.fn();
    const tokens: string[] = [];

    const result = await askVideoStream(3, "hi", { onSources, onToken: (text) => tokens.push(text) });

    expect(onSources).toHaveBeenCalledWith([]);
    expect(tokens).toEqual(["Xin ", "chào"]);
    expect(result.status).toBe("answered");
    expect(result.answer).toBe("Xin chào");

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toMatch(/\/api\/v1\/search\/videos\/3\/rag\/stream$/);
    expect(init.method).toBe("POST");
    expect(init.headers.Authorization).toBe("Bearer token-123");
    expect(JSON.parse(init.body)).toEqual({ query: "hi", top_k: 5 });
  });

  it("reports STREAM_UNAVAILABLE for a non-2xx response so the caller can fall back", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("not found", { status: 404 })));

    await expect(askVideoStream(3, "hi", { onToken: () => {} })).rejects.toMatchObject({
      code: STREAM_UNAVAILABLE,
    });
  });

  it("reports STREAM_UNAVAILABLE when the request can't be sent at all", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(askVideoStream(3, "hi", { onToken: () => {} })).rejects.toMatchObject({
      code: STREAM_UNAVAILABLE,
    });
  });

  it("rejects with a plain error (no fallback) when the stream ends without a final result", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse('event: token\ndata: {"text":"par"}\n\n')));

    const error = await askVideoStream(3, "hi", { onToken: () => {} }).catch((e) => e);

    expect(error).toBeInstanceOf(Error);
    expect(error.code).toBeUndefined();
    expect(error.message).toMatch(/cut off/i);
  });
});
