export interface SseEvent {
  event: string;
  data: string;
}

/**
 * Parse a Server-Sent Events body (the `text/event-stream` format the
 * streaming RAG endpoint writes) into `{event, data}` frames as they
 * arrive. Works on a fetch `Response.body`, so it supports POST
 * requests with an Authorization header - which the browser's built-in
 * EventSource (GET-only, no custom headers) can't do.
 *
 * Frames are separated by a blank line; a frame's `event:` line names
 * it (default "message") and its `data:` lines are joined with "\n".
 * Comment lines (starting with ":") are ignored.
 */
export async function* readSseEvents(stream: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const frame = parseFrame(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        if (frame) yield frame;
        boundary = buffer.indexOf("\n\n");
      }
    }

    const tail = parseFrame((buffer + decoder.decode()).trim());
    if (tail) yield tail;
  } finally {
    reader.releaseLock();
  }
}

function parseFrame(raw: string): SseEvent | null {
  if (!raw) return null;
  let event = "message";
  const data: string[] = [];

  for (const line of raw.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    const value = colon === -1 ? "" : line.slice(colon + 1).replace(/^ /, "");
    if (field === "event") event = value;
    else if (field === "data") data.push(value);
  }

  if (data.length === 0) return null;
  return { event, data: data.join("\n") };
}
