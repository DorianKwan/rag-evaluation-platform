import { z } from "zod";

export const SupportedMetric = z.enum([
  "faithfulness",
  "answer_relevancy",
  "context_precision",
  "context_recall",
]);

export type SupportedMetric = z.infer<typeof SupportedMetric>;

export const EvaluateRequest = z.object({
  user_input: z.string().min(1),
  reference: z.string().min(1),
  trace_id: z.string().optional(),
});

export type EvaluateRequest = z.infer<typeof EvaluateRequest>;

export const EvaluateResponse = z.object({
  trace_id: z.string(),
  scores: z.record(SupportedMetric, z.number().min(0).max(1)),
});

export type EvaluateResponse = z.infer<typeof EvaluateResponse>;
