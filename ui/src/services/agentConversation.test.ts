import { afterEach, describe, expect, it, vi } from "vitest";

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("./index", () => ({
  default: apiMock,
}));

import {
  conversationHistoryApi,
  visitorApi,
} from "./agentConversation";

afterEach(() => {
  apiMock.get.mockReset();
  apiMock.post.mockReset();
  apiMock.delete.mockReset();
});

describe("agentConversation service", () => {
  it("加载会话详情时应编码 sessionId，避免斜杠或中文打断路由", async () => {
    apiMock.get.mockResolvedValueOnce({ sessionId: "session/中文 id" });

    await conversationHistoryApi.getSessionDetail("session/中文 id");

    expect(apiMock.get).toHaveBeenCalledWith(
      "/api/agent/conversation/sessions/session%2F%E4%B8%AD%E6%96%87%20id"
    );
  });

  it("访客命名应发送后端约定的 visitorName 字段并保留 visitorId", async () => {
    apiMock.post.mockResolvedValueOnce({ username: "测试用户" });

    await visitorApi.naming("测试用户", "visitor-existing");

    expect(apiMock.post).toHaveBeenCalledWith(
      "/api/agent/visitor/naming",
      { visitorName: "测试用户", visitorId: "visitor-existing" }
    );
  });
});
