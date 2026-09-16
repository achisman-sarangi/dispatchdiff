import type {
  Driver,
  Load,
  OperationalDisruption,
  PlanBuildResult,
  ReplanResult,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Validator<T> = (value: unknown) => value is T;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isDriverArray(value: unknown): value is Driver[] {
  return Array.isArray(value) && value.every((item) => isRecord(item) && typeof item.id === "string");
}

function isLoadArray(value: unknown): value is Load[] {
  return Array.isArray(value) && value.every((item) => isRecord(item) && typeof item.id === "string");
}

function isPlanBuildResult(value: unknown): value is PlanBuildResult {
  return isRecord(value) && isRecord(value.plan) && Array.isArray(value.plan.assignments) &&
    Array.isArray(value.unassigned_load_ids) && isRecord(value.evaluation_summary);
}

function isDisruption(value: unknown): value is OperationalDisruption {
  return isRecord(value) && typeof value.id === "string" && typeof value.driver_id === "string" &&
    typeof value.type === "string" && typeof value.occurred_at === "string";
}

function isReplanResult(value: unknown): value is ReplanResult {
  return isRecord(value) && isRecord(value.previous_plan) && isRecord(value.proposed_plan) &&
    Array.isArray(value.impacted_assignments) && Array.isArray(value.assignment_changes) &&
    isRecord(value.metrics) && isRecord(value.metrics.before_metrics) &&
    isRecord(value.metrics.after_metrics) && isRecord(value.metrics.delta);
}

async function request<T>(path: string, validator: Validator<T>, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError("DispatchDiff API request failed.", response.status);
  }
  try {
    const body: unknown = await response.json();
    if (!validator(body)) {
      throw new ApiError("DispatchDiff API returned malformed data.", response.status);
    }
    return body;
  } catch (error: unknown) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(
      error instanceof Error ? "DispatchDiff API returned malformed data." : "Invalid response.",
      response.status,
    );
  }
}

export const getDrivers = (): Promise<Driver[]> => request("/api/demo/drivers", isDriverArray);
export const getLoads = (): Promise<Load[]> => request("/api/demo/loads", isLoadArray);
export const getDemoPlan = (): Promise<PlanBuildResult> =>
  request("/api/demo/plan", isPlanBuildResult);
export const getDemoDisruption = (): Promise<OperationalDisruption> =>
  request("/api/demo/disruption", isDisruption);
export const runDemoReplan = (): Promise<ReplanResult> =>
  request("/api/demo/replan", isReplanResult, { method: "POST" });
