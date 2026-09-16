import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../api/client";
import typeSource from "../api/types.ts?raw";
import { disruption, drivers, loads, plan, replan } from "../test/fixtures";
import { CommandCenter } from "./CommandCenter";

vi.mock("../api/client", () => ({
  getDrivers: vi.fn(),
  getLoads: vi.fn(),
  getDemoPlan: vi.fn(),
  getDemoDisruption: vi.fn(),
  runDemoReplan: vi.fn(),
}));

const mockedApi = vi.mocked(api);

function resolveInitialData() {
  mockedApi.getDrivers.mockResolvedValue(drivers);
  mockedApi.getLoads.mockResolvedValue(loads);
  mockedApi.getDemoPlan.mockResolvedValue(plan);
  mockedApi.getDemoDisruption.mockResolvedValue(disruption);
  mockedApi.runDemoReplan.mockResolvedValue(replan);
}

async function renderLoaded() {
  render(<CommandCenter />);
  await screen.findByRole("heading", { name: "Current Fleet Plan" });
}

async function runReplan() {
  await renderLoaded();
  await userEvent.click(screen.getByRole("button", { name: "Run Re-plan" }));
  await screen.findByRole("heading", { name: "Impact Summary" });
}

describe("CommandCenter", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    resolveInitialData();
  });

  it("renders the initial page identity", async () => {
    await renderLoaded();
    expect(screen.getByRole("heading", { name: "DispatchDiff" })).toBeInTheDocument();
    expect(screen.getByText("Explainable exception handling for fleet re-planning")).toBeInTheDocument();
  });

  it("announces the loading state", () => {
    mockedApi.getDrivers.mockReturnValue(new Promise(() => undefined));
    render(<CommandCenter />);
    expect(screen.getByRole("status")).toHaveTextContent("Connecting to planning service");
  });

  it("renders the current fleet plan", async () => {
    await renderLoaded();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getAllByText("LOAD-001").length).toBeGreaterThan(0);
    expect(screen.getByText("$8,800")).toBeInTheDocument();
  });

  it("renders the pending canonical disruption", async () => {
    await renderLoaded();
    expect(screen.getByRole("heading", { name: "Incoming operational disruption" })).toBeInTheDocument();
    expect(screen.getByText("+180 min")).toBeInTheDocument();
    expect(screen.getByText("Customer detention at previous stop")).toBeInTheDocument();
  });

  it("runs the demo replan", async () => {
    await runReplan();
    expect(mockedApi.runDemoReplan).toHaveBeenCalledOnce();
    expect(screen.getByRole("heading", { name: "Impact Summary" })).toBeInTheDocument();
  });

  it("renders impact counts from the backend", async () => {
    await runReplan();
    expect(screen.getByText("assignment invalidated").previousSibling).toHaveTextContent("1");
    expect(screen.getByText("assignments preserved").previousSibling).toHaveTextContent("4");
    expect(screen.getByText("new assignments created").previousSibling).toHaveTextContent("2");
  });

  it("shows the removed assignment and reason", async () => {
    await runReplan();
    const removed = screen.getByRole("heading", { name: "REMOVED" }).closest("article");
    expect(removed).not.toBeNull();
    expect(within(removed!).getByRole("heading", { name: "DRV-001 LOAD-001" })).toBeInTheDocument();
    expect(within(removed!).getByText("PICKUP_WINDOW_MISSED")).toBeInTheDocument();
  });

  it("shows replacement assignments", async () => {
    await runReplan();
    expect(screen.getByText(/Load LOAD-001 reassigned from Driver DRV-001 to Driver DRV-007/)).toBeInTheDocument();
    expect(screen.getByText(/Load LOAD-007 assigned to Driver DRV-001/)).toBeInTheDocument();
  });

  it("shows preserved assignments", async () => {
    await runReplan();
    expect(screen.getByText("Existing work left exactly as planned")).toBeInTheDocument();
    expect(screen.getByText("Assignment preserved because it remains feasible and was not affected by the disruption.")).toBeInTheDocument();
  });

  it("renders before and after business metrics", async () => {
    await runReplan();
    const revenue = screen.getByRole("heading", { name: "Revenue" }).closest("article");
    expect(revenue).not.toBeNull();
    expect(within(revenue!).getByText("$8,800")).toBeInTheDocument();
    expect(within(revenue!).getByText("$10,700")).toBeInTheDocument();
    expect(within(revenue!).getByText("+$1,900")).toBeInTheDocument();
  });

  it("labels increased deadhead as a tradeoff", async () => {
    await runReplan();
    const deadhead = screen.getByRole("heading", { name: "Deadhead" }).closest("article");
    expect(deadhead).not.toBeNull();
    expect(within(deadhead!).getByText("Operational tradeoff: more empty travel")).toBeInTheDocument();
    expect(within(deadhead!).getByText("+30 min")).toBeInTheDocument();
  });

  it("approves the proposal in local state", async () => {
    await runReplan();
    await userEvent.click(screen.getByRole("button", { name: "Approve Re-plan" }));
    expect(screen.getByText(/Re-plan approved/, { selector: ".status-banner" })).toBeInTheDocument();
    expect(screen.getByText("Local decision recorded")).toBeInTheDocument();
  });

  it("rejects the proposal in local state", async () => {
    await runReplan();
    await userEvent.click(screen.getByRole("button", { name: "Keep Current Plan" }));
    expect(screen.getByText(/Current plan retained — invalidated assignment remains/)).toBeInTheDocument();
    expect(screen.getByText("Current invalid assignment remains")).toBeInTheDocument();
  });

  it("shows an API error and retries", async () => {
    mockedApi.getDrivers.mockRejectedValueOnce(new Error("offline"));
    render(<CommandCenter />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to reach planning service");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(mockedApi.getDrivers).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: "Current Fleet Plan" })).toBeInTheDocument();
  });

  it("does not use any in core API contracts", () => {
    expect(apiTypeHasAny(apiTypeWithoutComments(apiTypeNormalize(apiTypeSource())))).toBe(false);
  });
});

function apiTypeSource(): string { return typeSource; }
function apiTypeNormalize(value: string): string { return value.replace(/\s+/g, " "); }
function apiTypeWithoutComments(value: string): string { return value.replace(/\/\/.*|\/\*[\s\S]*?\*\//g, ""); }
function apiTypeHasAny(value: string): boolean { return /\bany\b/.test(value); }
