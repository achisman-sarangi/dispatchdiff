import { useCallback, useEffect, useState } from "react";

import { getDemoDisruption, getDemoPlan, getDrivers, getLoads, runDemoReplan } from "../api/client";
import type { Driver, Load, OperationalDisruption, PlanBuildResult, ReplanResult } from "../api/types";
import { AppShell } from "../components/AppShell";
import { DecisionPanel, type DecisionState } from "../components/DecisionPanel";
import { DisruptionCard } from "../components/DisruptionCard";
import { EventTimeline, type TimelineEvent } from "../components/EventTimeline";
import { FleetPlanTable } from "../components/FleetPlanTable";
import { Header } from "../components/Header";
import { ImpactSummary } from "../components/ImpactSummary";
import { MetricsComparison } from "../components/MetricCard";
import { PlanDiff } from "../components/PlanDiff";
import { StatusBanner } from "../components/StatusBanner";
import { formatMoney, routeLabel } from "../utils/format";

interface DemoData { drivers: Driver[]; loads: Load[]; plan: PlanBuildResult; disruption: OperationalDisruption; }

const INITIAL_EVENTS: TimelineEvent[] = [
  { label: "Plan loaded", detail: "Baseline fleet assignments validated" },
  { label: "Current plan ready", detail: "Planning service reports healthy" },
];

export function CommandCenter() {
  const [data, setData] = useState<DemoData | null>(null);
  const [result, setResult] = useState<ReplanResult | null>(null);
  const [decision, setDecision] = useState<DecisionState>("PENDING");
  const [events, setEvents] = useState<TimelineEvent[]>(INITIAL_EVENTS);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDemo = useCallback(async () => {
    setLoading(true); setError(null); setResult(null); setDecision("PENDING"); setEvents(INITIAL_EVENTS);
    try {
      const [drivers, loads, plan, disruption] = await Promise.all([getDrivers(), getLoads(), getDemoPlan(), getDemoDisruption()]);
      setData({ drivers, loads, plan, disruption });
    } catch (requestError: unknown) {
      console.error("Unable to load DispatchDiff demo data", requestError);
      setData(null); setError("Unable to reach planning service. Check the backend connection and retry.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void loadDemo(); }, [loadDemo]);

  async function runReplan() {
    if (!data) return;
    setRunning(true); setError(null);
    try {
      const replan = await runDemoReplan();
      setResult(replan); setDecision("PENDING");
      const impacted = replan.impacted_assignments[0];
      const replacement = replan.added_assignments.find((item) => item.load_id === impacted?.load_id);
      setEvents([...INITIAL_EVENTS,
        { label: "Detention received", detail: `${replan.disruption.driver_id} delayed ${replan.disruption.detention_minutes ?? 0} minutes` },
        { label: "Constraint failure detected", detail: impacted?.reasons[0]?.code ?? "Assignment infeasible" },
        { label: `${impacted?.load_id ?? "Load"} reassigned`, detail: replacement ? `${replacement.driver_id} selected as replacement` : "Affected work evaluated" },
        { label: "Proposed plan generated", detail: `${replan.preserved_assignments.length} assignments preserved` },
      ]);
    } catch (requestError: unknown) {
      console.error("Unable to run DispatchDiff re-plan", requestError);
      setError("The re-plan could not be generated. The current plan has not changed.");
    } finally { setRunning(false); }
  }

  function recordDecision(nextDecision: Exclude<DecisionState, "PENDING">) {
    setDecision(nextDecision);
    setEvents((current) => [...current, { label: nextDecision === "APPROVED" ? "Re-plan approved" : "Current plan retained", detail: nextDecision === "APPROVED" ? "Local decision recorded" : "Current invalid assignment remains" }]);
  }

  const affectedAssignment = data?.plan.plan.assignments.find((item) => item.driver_id === data.disruption.driver_id);
  const affectedLoad = data?.loads.find((load) => load.id === affectedAssignment?.load_id);
  const driver = data?.drivers.find((item) => item.id === data.disruption.driver_id);
  const apiOnline = data !== null && !error;

  return (
    <AppShell drivers={data?.drivers.length ?? 0} loads={data?.loads.length ?? 0} apiOnline={apiOnline}>
      <div className="workspace-shell">
        <Header apiOnline={apiOnline} onReset={() => void loadDemo()} />
        <main className="main-content" id="overview">
          {loading && <div className="loading-state" role="status"><span className="loading-pulse" aria-hidden="true" />Connecting to planning service…</div>}
          {error && <StatusBanner tone="error"><span>{error}</span><button className="button compact" type="button" onClick={() => void loadDemo()}>Retry</button></StatusBanner>}
          {data && !loading && <>
            <header className="workspace-heading"><div><p className="panel-kicker">Operations overview</p><h2>Fleet control center</h2><p>Explainable exception handling for fleet re-planning</p></div><time>Demo plan · Mar 10, 2025</time></header>
            {decision === "APPROVED" && <StatusBanner tone="success">✓ Re-plan approved — proposed plan selected for demo</StatusBanner>}
            {decision === "REJECTED" && <StatusBanner tone="warning">Current plan retained — invalidated assignment remains</StatusBanner>}

            {!result && <>
              <section className="plan-health" aria-label="Plan Health"><div className="health-title"><span className="status-dot" />Plan Health</div><HealthMetric label="Assigned" value={String(data.plan.evaluation_summary.assigned_loads)} /><HealthMetric label="Open" value={String(data.plan.evaluation_summary.unassigned_loads)} /><HealthMetric label="Revenue" value={formatMoney(data.plan.evaluation_summary.total_revenue_cents)} /><HealthMetric label="Deadhead" value={`${data.plan.evaluation_summary.total_deadhead_minutes} min`} /></section>
              <div className="overview-grid">
                <section className="surface-panel active-plan" id="fleet-plan"><PanelHeader title="Current Fleet Plan" subtitle="Active Fleet Plan · Current assignments before operational exceptions" count={`${data.plan.plan.assignments.length} active`} /><FleetPlanTable planResult={data.plan} drivers={data.drivers} loads={data.loads} /></section>
                <section id="exceptions"><DisruptionCard disruption={data.disruption} result={result} running={running} onRun={() => void runReplan()} driverName={driver?.name ?? data.disruption.driver_id} affectedLoad={affectedAssignment?.load_id ?? "—"} affectedLane={affectedLoad ? routeLabel(affectedLoad.origin_city, affectedLoad.origin_state, affectedLoad.destination_city, affectedLoad.destination_state) : "Route unavailable"} /></section>
              </div>
            </>}

            {result && <>
              <section className="recovery-banner"><div className="recovery-icon" aria-hidden="true">✓</div><div><p className="panel-kicker">Plan recovered</p><h2 id="impact-title">Impact Summary</h2><p>The disrupted load remains covered with no late deliveries or HOS violations.</p></div><ImpactSummary result={result} /></section>
              <div className="decision-workspace">
                <section className="surface-panel changes-panel"><PanelHeader title="Plan Changes" subtitle="Targeted recovery of affected work" count={`${result.removed_assignments.length + result.added_assignments.length} changes`} /><PlanDiff result={result} loads={data.loads} /></section>
                <aside className="impact-rail"><section className="surface-panel"><PanelHeader title="Operational Impact" subtitle="Before and proposed plan" /><MetricsComparison before={result.metrics.before_metrics} after={result.metrics.after_metrics} delta={result.metrics.delta} /><div className="tradeoff-panel"><span>Tradeoff</span><strong>Additional empty travel · +{result.metrics.delta.deadhead_minutes_delta} min deadhead</strong><p>The replacement keeps the disrupted load covered and increases fleet utilization, at the cost of additional empty travel.</p></div></section><EventTimeline events={events} /></aside>
              </div>
              <div id="decision-log"><DecisionPanel preservedCount={result.preserved_assignments.length} decision={decision} onApprove={() => recordDecision("APPROVED")} onReject={() => recordDecision("REJECTED")} /></div>
            </>}
          </>}
        </main>
      </div>
    </AppShell>
  );
}

function HealthMetric({ label, value }: { label: string; value: string }) { return <div className="health-metric"><span>{label}</span><strong>{value}</strong></div>; }
function PanelHeader({ title, subtitle, count }: { title: string; subtitle: string; count?: string }) { return <header className="panel-header"><div><h2>{title}</h2><p>{subtitle}</p></div>{count && <span>{count}</span>}</header>; }
