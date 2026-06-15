import { afterEach, describe, expect, it, vi } from "vitest";

const requestMock = vi.hoisted(() => ({
  post: vi.fn(),
}));

vi.mock("@/utils/request", () => ({
  default: requestMock,
}));

import { agentFileApi } from "./agentFile";

afterEach(() => {
  requestMock.post.mockReset();
});

describe("agentFile service", () => {
  it("上传附件时应让浏览器自动生成 multipart boundary", async () => {
    requestMock.post.mockResolvedValueOnce({ name: "notes.txt" });

    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    await agentFileApi.uploadConversationFile("session-1", file);

    expect(requestMock.post).toHaveBeenCalledTimes(1);
    const [url, formData, config] = requestMock.post.mock.calls[0] ?? [];

    expect(url).toBe("/api/agent/file/upload");
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get("sessionId")).toBe("session-1");
    expect(formData.get("file")).toBe(file);
    expect(config).toBeUndefined();
  });
});
