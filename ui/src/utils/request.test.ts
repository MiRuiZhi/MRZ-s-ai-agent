import { beforeEach, describe, expect, it, vi } from "vitest";

const axiosMock = vi.hoisted(() => ({
  create: vi.fn(),
}));

const fakeRequestInstance = vi.hoisted(() => ({
  interceptors: {
    request: {
      use: vi.fn(),
    },
    response: {
      use: vi.fn(),
    },
  },
}));

vi.mock("axios", () => ({
  default: axiosMock,
}));

vi.mock("@/services/agentConversation", () => ({
  getDeviceId: () => "device-test",
}));

vi.mock("./origin", () => ({
  resolveServiceBaseUrl: () => "",
}));

vi.mock("./utils", () => ({
  showMessage: () => undefined,
}));

describe("request client", () => {
  beforeEach(() => {
    vi.resetModules();
    axiosMock.create.mockReset();
    fakeRequestInstance.interceptors.request.use.mockReset();
    fakeRequestInstance.interceptors.response.use.mockReset();
    axiosMock.create.mockReturnValue(fakeRequestInstance);
  });

  it("不应全局强制 JSON Content-Type，避免 FormData 上传丢失 multipart boundary", async () => {
    await import("./request");

    expect(axiosMock.create).toHaveBeenCalledWith(
      expect.not.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      })
    );
  });
});
