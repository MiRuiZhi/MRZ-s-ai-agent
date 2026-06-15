import { afterEach, describe, expect, it, vi } from "vitest";

const fetchEventSourceMock = vi.hoisted(() => vi.fn());

vi.mock("@microsoft/fetch-event-source", () => ({
  fetchEventSource: fetchEventSourceMock,
}));

import querySSE, { buildSseUrl } from "./querySSE";

afterEach(() => {
  fetchEventSourceMock.mockReset();
  vi.unstubAllGlobals();
});

describe("querySSE", () => {
  it("builds same-origin SSE URLs from normalized service base", () => {
    vi.stubGlobal("window", {
      location: {
        hostname: "localhost",
      },
    });

    expect(buildSseUrl("/data/chatQuery", "http://127.0.0.1:8000")).toBe(
      "http://localhost:8000/data/chatQuery"
    );
    expect(buildSseUrl("/data/chatQuery", "")).toBe("/data/chatQuery");
  });

  it("stops the stream after an SSE error so fetch-event-source will not retry forever", () => {
    fetchEventSourceMock.mockResolvedValueOnce(undefined);
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    const handleError = vi.fn();
    const handleClose = vi.fn();

    querySSE({
      body: { query: "hello" },
      handleMessage: vi.fn(),
      handleError,
      handleClose,
    });

    const options = fetchEventSourceMock.mock.calls[0]?.[1];
    expect(() => options.onerror(new Error("network down"))).toThrow("network down");
    expect(options.signal.aborted).toBe(true);
    expect(handleError).toHaveBeenCalledTimes(1);
    expect(handleError.mock.calls[0]?.[0]).toEqual(new Error("network down"));
  });
});
