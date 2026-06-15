import { z } from "zod";

type SimpleAgentFrame = {
  messageType: string;
  data?: unknown;
  isFinal: boolean;
  messageId?: string;
  resultMap: Record<string, unknown>;
};

let syntheticEventSeq = 0;

const answerEnvelopeSchema = z.object({
  status: z.string(),
  packageType: z.string(),
  finished: z.boolean(),
  errorMsg: z.string().nullable().optional().transform((value) => value ?? ""),
  resultMap: z.object({ eventData: z.unknown().optional() }).passthrough().optional().default({}),
}).passthrough();

const simpleAgentFrameSchema = z.object({
  messageType: z.string(),
  data: z.unknown().optional(),
  isFinal: z.boolean().optional().default(false),
  messageId: z.string().optional(),
  resultMap: z.record(z.string(), z.unknown()).optional().default({}),
}).passthrough();

const eventDataSchema = z.object({
  messageOrder: z.number(),
  messageType: z.string(),
  messageId: z.string(),
  taskId: z.string(),
  taskOrder: z.number(),
  resultMap: z.object({ messageType: z.string().optional() }).passthrough(),
  artifactRefs: z.array(z.object({}).passthrough()).optional(),
}).passthrough();

const dataChatEventSchema = z.discriminatedUnion("eventType", [
  z.object({
    eventType: z.literal("THINK"),
    data: z.string(),
  }),
  z.object({
    eventType: z.literal("CHART_DATA"),
    data: z.array(z.record(z.string(), z.unknown())),
  }),
  z.object({
    eventType: z.literal("ERROR"),
    data: z.string(),
  }),
  z.object({
    eventType: z.literal("READY"),
    data: z.unknown().optional(),
  }),
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function readStringField(record: Record<string, unknown>, key: string): string | undefined {
  return asString(record[key]);
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => String(item)).filter(Boolean)
    : [];
}

function normalizePlanStatus(value: unknown): MESSAGE.PlanStatus {
  if (value === "completed" || value === "in_progress" || value === "not_started") {
    return value;
  }
  if (value === "running") {
    return "in_progress";
  }
  return "not_started";
}

function resolveTextPayload(data: unknown): string {
  if (typeof data === "string") {
    return data;
  }
  if (!isRecord(data)) {
    return "";
  }
  return (
    readStringField(data, "taskSummary") ||
    readStringField(data, "result") ||
    readStringField(data, "summary") ||
    readStringField(data, "content") ||
    readStringField(data, "currentStep") ||
    ""
  );
}

function nextSyntheticId(messageType: string) {
  syntheticEventSeq += 1;
  return `simple-${messageType}-${syntheticEventSeq}`;
}

function resolveTaskId(frame: SimpleAgentFrame, messageId: string) {
  const data = isRecord(frame.data) ? frame.data : {};
  return (
    asString(frame.resultMap.taskId) ||
    readStringField(data, "taskId") ||
    `task-${messageId}`
  );
}

function resolveRequestId(frame: SimpleAgentFrame) {
  const data = isRecord(frame.data) ? frame.data : {};
  return (
    asString(frame.resultMap.requestId) ||
    readStringField(data, "requestId") ||
    ""
  );
}

function buildPlanTask(frame: SimpleAgentFrame, messageId: string) {
  const payload = isRecord(frame.data) ? frame.data : {};
  const steps = readStringArray(payload.steps);
  const stages = readStringArray(payload.stages);
  const normalizedSteps = steps.length ? steps : stages;
  const normalizedStages = stages.length ? stages : normalizedSteps;
  const rawStepStatus = Array.isArray(payload.stepStatus)
    ? payload.stepStatus
    : normalizedSteps.map(() => "not_started");

  return {
    id: messageId,
    messageId,
    requestId: resolveRequestId(frame),
    messageTime: String(Date.now()),
    messageType: "plan",
    finish: frame.isFinal,
    isFinal: frame.isFinal,
    title:
      readStringField(payload, "title") ||
      readStringField(payload, "currentStep") ||
      "执行计划",
    notes: readStringArray(payload.notes),
    stages: normalizedStages,
    steps: normalizedSteps,
    stepStatus: normalizedSteps.map((_, index) => normalizePlanStatus(rawStepStatus[index])),
  } as unknown as MESSAGE.Task;
}

function buildSimpleTask(frame: SimpleAgentFrame, messageId: string) {
  const nestedPayload = isRecord(frame.data) ? frame.data : {};
  const nestedType = readStringField(nestedPayload, "messageType") || frame.messageType;
  const resultText = resolveTextPayload(frame.data);
  const task: Record<string, unknown> = {
    ...nestedPayload,
    id: messageId,
    messageId,
    requestId: resolveRequestId(frame),
    messageTime: String(Date.now()),
    messageType: nestedType,
    finish: frame.isFinal,
    isFinal: frame.isFinal,
    result: resultText,
  };

  if (nestedType === "tool_thought") {
    task.toolThought = resultText;
  }
  if (nestedType === "plan_thought") {
    task.planThought = resultText;
  }
  if (nestedType === "task") {
    task.task = resultText;
  }
  if (nestedType === "result" || nestedType === "task_summary") {
    task.taskSummary = readStringField(nestedPayload, "taskSummary") || resultText;
    task.fileList = Array.isArray(nestedPayload.fileList) ? nestedPayload.fileList : [];
  }

  return task as unknown as MESSAGE.Task;
}

function toLegacyAnswer(frame: SimpleAgentFrame): MESSAGE.Answer {
  const messageId = frame.messageId || nextSyntheticId(frame.messageType);
  const eventDataMessageType =
    frame.messageType === "plan" || frame.messageType === "plan_thought"
      ? frame.messageType
      : "task";
  const eventData = {
    messageOrder: syntheticEventSeq,
    messageType: eventDataMessageType,
    messageId,
    taskId: resolveTaskId(frame, messageId),
    taskOrder: 1,
    resultMap:
      frame.messageType === "plan"
        ? buildPlanTask(frame, messageId)
        : buildSimpleTask(frame, messageId),
  } satisfies MESSAGE.EventData;

  return {
    status: frame.isFinal ? "success" : "running",
    response: "",
    responseAll: "",
    finished: frame.isFinal,
    useTimes: 0,
    useTokens: 0,
    resultMap: {
      ...frame.resultMap,
      eventData,
    },
    responseType: "text",
    voiceUrl: "",
    traceId: "",
    encrypted: false,
    runningLog: "",
    query: "",
    messages: "",
    packageType: "result",
    errorMsg: "",
  } as MESSAGE.Answer;
}

/**
 * 这里只校验 SSE 顶层协议骨架，内部 payload 继续交给业务解析层消费，
 * 避免前端跟后端富结构结果做过紧耦合。
 */
export function parseAgentAnswer(raw: unknown): MESSAGE.Answer {
  if (isRecord(raw) && "status" in raw && "packageType" in raw && "finished" in raw) {
    return answerEnvelopeSchema.parse(raw) as unknown as MESSAGE.Answer;
  }
  return toLegacyAnswer(simpleAgentFrameSchema.parse(raw));
}

/**
 * SSE eventData 入口统一做一次骨架校验，确保 message/task 主键存在，
 * 后续 combineData 只处理结构合法的事件。
 */
export function parseEventData(raw: unknown): MESSAGE.EventData {
  return eventDataSchema.parse(raw) as unknown as MESSAGE.EventData;
}

export function parseDataChatEvent(raw: unknown): CHAT.DataChatEvent {
  return dataChatEventSchema.parse(raw);
}
