import { describe, expect, it } from "vitest";

import { readSseEvents, type SseEvent } from "@/lib/sse";

/** A ReadableStream that delivers `chunks` one by one, like a network body. */
function streamOf(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<SseEvent[]> {
  const events: SseEvent[] = [];
  for await (const event of readSseEvents(stream)) events.push(event);
  return events;
}

describe("readSseEvents", () => {
  it("parses named events with JSON data", async () => {
    const events = await collect(
      streamOf(['event: token\ndata: {"text":"Lạm "}\n\n', 'event: done\ndata: {"status":"answered"}\n\n']),
    );

    expect(events).toEqual([
      { event: "token", data: '{"text":"Lạm "}' },
      { event: "done", data: '{"status":"answered"}' },
    ]);
  });

  it("reassembles a frame split across network chunks, including a split multi-byte character", async () => {
    const bytes = new TextEncoder().encode('event: token\ndata: {"text":"phát"}\n\n');
    const splitAt = bytes.indexOf(0xc3) + 1; // inside the 2-byte "á"
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(bytes.slice(0, splitAt));
        controller.enqueue(bytes.slice(splitAt));
        controller.close();
      },
    });

    expect(await collect(stream)).toEqual([{ event: "token", data: '{"text":"phát"}' }]);
  });

  it("handles CRLF line endings, comments, default event names and multi-line data", async () => {
    const events = await collect(
      streamOf([": keep-alive\r\n\r\n", "data: first\r\ndata: second\r\n\r\n"]),
    );

    expect(events).toEqual([{ event: "message", data: "first\nsecond" }]);
  });

  it("yields a final frame even without a trailing blank line", async () => {
    const events = await collect(streamOf(['event: done\ndata: {"status":"answered"}']));

    expect(events).toEqual([{ event: "done", data: '{"status":"answered"}' }]);
  });
});
