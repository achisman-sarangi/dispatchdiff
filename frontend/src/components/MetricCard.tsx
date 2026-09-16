import type { PlanMetricDelta, PlanMetrics } from "../api/types";
import { formatMinutes, formatMoney, formatSigned } from "../utils/format";

type MetricTone = "positive" | "tradeoff" | "neutral";

interface MetricCardProps {
  label: string;
  before: string;
  after: string;
  delta: string;
  tone: MetricTone;
  interpretation: string;
}

export function MetricCard({
  label,
  before,
  after,
  delta,
  tone,
  interpretation,
}: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-heading">
        <h3>{label}</h3>
        <span className={`metric-delta ${tone}`}>{delta}</span>
      </div>
      <div className="metric-comparison"><span>{before}</span><b aria-hidden="true">→</b><strong>{after}</strong></div>
      <p className={`metric-interpretation ${tone}`}>{interpretation}</p>
    </article>
  );
}

export function MetricsComparison({
  before,
  after,
  delta,
}: {
  before: PlanMetrics;
  after: PlanMetrics;
  delta: PlanMetricDelta;
}) {
  const cards: MetricCardProps[] = [
    {
      label: "Coverage",
      before: String(before.assigned_loads),
      after: String(after.assigned_loads),
      delta: formatSigned(delta.assigned_loads_delta),
      tone: delta.assigned_loads_delta > 0 ? "positive" : "neutral",
      interpretation: delta.assigned_loads_delta > 0 ? "Fleet coverage improved" : "Coverage unchanged",
    },
    {
      label: "Unassigned loads",
      before: String(before.unassigned_loads),
      after: String(after.unassigned_loads),
      delta: formatSigned(delta.unassigned_loads_delta),
      tone: delta.unassigned_loads_delta < 0 ? "positive" : "neutral",
      interpretation: delta.unassigned_loads_delta < 0 ? "Fewer loads uncovered" : "Coverage unchanged",
    },
    {
      label: "Revenue",
      before: formatMoney(before.total_revenue_cents),
      after: formatMoney(after.total_revenue_cents),
      delta: formatSigned(delta.revenue_cents_delta, formatMoney),
      tone: delta.revenue_cents_delta > 0 ? "positive" : "neutral",
      interpretation: delta.revenue_cents_delta > 0 ? "Revenue opportunity increased" : "Revenue unchanged",
    },
    {
      label: "Deadhead",
      before: formatMinutes(before.total_deadhead_minutes),
      after: formatMinutes(after.total_deadhead_minutes),
      delta: formatSigned(delta.deadhead_minutes_delta, formatMinutes),
      tone: delta.deadhead_minutes_delta > 0 ? "tradeoff" : "positive",
      interpretation: delta.deadhead_minutes_delta > 0 ? "Operational tradeoff: more empty travel" : "Empty travel reduced",
    },
    {
      label: "Committed uncovered",
      before: String(before.committed_loads_unassigned),
      after: String(after.committed_loads_unassigned),
      delta: formatSigned(delta.committed_loads_unassigned_delta),
      tone: delta.committed_loads_unassigned_delta < 0 ? "positive" : "neutral",
      interpretation: after.committed_loads_unassigned === 0 ? "All commitments covered" : "Commitments need attention",
    },
    {
      label: "HOS violations",
      before: String(before.hos_violations),
      after: String(after.hos_violations),
      delta: formatSigned(delta.hos_violations_delta),
      tone: delta.hos_violations_delta <= 0 ? "positive" : "tradeoff",
      interpretation: after.hos_violations === 0 ? "No HOS conflicts" : "HOS conflicts remain",
    },
    {
      label: "Late loads",
      before: String(before.late_loads),
      after: String(after.late_loads),
      delta: formatSigned(delta.late_loads_delta),
      tone: delta.late_loads_delta <= 0 ? "positive" : "tradeoff",
      interpretation: after.late_loads === 0 ? "No late deliveries" : "Late deliveries remain",
    },
  ];

  return <div className="metrics-grid">{cards.map((card) => <MetricCard key={card.label} {...card} />)}</div>;
}
