import { describe, expect, it } from "vitest";

import { buildDataAgentToggleSelection, buildSubmitPayload } from "./inputMode";

describe("inputMode", () => {
  it("深度研究模式应保留结构化输出类型并打开 deepThink", () => {
    expect(
      buildSubmitPayload({
        question: "帮我调研竞品",
        visibleMode: "research",
        isDataAgent: false,
        visibleOutputProduct: { type: "html" } as CHAT.Product,
        uploadedFiles: [],
        chatRole: null,
      })
    ).toMatchObject({
      outputStyle: "html",
      deepThink: true,
    });
  });

  it("数据分析开关已开启时应切回上一个标准输出模式", () => {
    expect(
      buildDataAgentToggleSelection({
        isDataAgent: true,
        visibleMode: "research",
        visibleOutputProduct: { type: "docs" } as CHAT.Product,
        dataAgentProduct: { type: "dataAgent" } as CHAT.Product,
      })
    ).toEqual({
      product: { type: "docs" },
      deepThink: true,
    });
  });

  it("数据分析开关未开启时应切入数据分析并关闭 deepThink", () => {
    expect(
      buildDataAgentToggleSelection({
        isDataAgent: false,
        visibleMode: "research",
        visibleOutputProduct: { type: "docs" } as CHAT.Product,
        dataAgentProduct: { type: "dataAgent" } as CHAT.Product,
      })
    ).toEqual({
      product: { type: "dataAgent" },
      deepThink: false,
    });
  });
});
