type InputModeKey = "quick" | "think" | "research";

export function buildSubmitPayload(params: {
  question: string;
  visibleMode: InputModeKey;
  isDataAgent: boolean;
  visibleOutputProduct: CHAT.Product;
  uploadedFiles: CHAT.TFile[];
  chatRole: CHAT.ConversationRole | null;
}) {
  const outputStyle = params.isDataAgent
    ? "dataAgent"
    : params.visibleMode === "quick"
      ? "chat"
      : params.visibleOutputProduct.type;

  return {
    message: params.question.trim(),
    outputStyle,
    deepThink:
      outputStyle !== "chat" && outputStyle !== "dataAgent"
        ? params.visibleMode === "research"
        : false,
    files: params.uploadedFiles.length > 0 ? params.uploadedFiles : undefined,
    aiAgentId: outputStyle === "chat" ? params.chatRole?.agentId : undefined,
  };
}

export function buildDataAgentToggleSelection(params: {
  isDataAgent: boolean;
  visibleMode: InputModeKey;
  visibleOutputProduct: CHAT.Product;
  dataAgentProduct: CHAT.Product;
}) {
  if (params.isDataAgent) {
    return {
      product: params.visibleOutputProduct,
      deepThink: params.visibleMode === "research",
    };
  }

  return {
    product: params.dataAgentProduct,
    deepThink: false,
  };
}
