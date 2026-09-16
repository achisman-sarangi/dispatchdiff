import type { ReplanResult } from "../api/types";

export function ImpactSummary({ result }: { result: ReplanResult }) {
  const violation = result.impacted_assignments[0]?.reasons[0];
  return (
    <div className="recovery-summary">
      <div className="impact-grid">
        <ImpactNumber value={result.impacted_assignments.length} label="assignment invalidated" />
        <ImpactNumber value={result.preserved_assignments.length} label="assignments preserved" />
        <ImpactNumber value={result.added_assignments.length} label="new assignments created" />
        <ImpactNumber value={result.metrics.after_metrics.committed_loads_unassigned} label="committed loads uncovered" />
      </div>
      {violation && <span className="reason-code recovery-reason">{violation.code}</span>}
    </div>
  );
}

function ImpactNumber({ value, label }: { value: number; label: string }) {
  return <div><strong>{value}</strong><span>{label}</span></div>;
}
