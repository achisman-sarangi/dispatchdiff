import type { OperationalDisruption, ReplanResult } from "../api/types";

interface DisruptionCardProps {
  disruption: OperationalDisruption;
  result: ReplanResult | null;
  running: boolean;
  onRun: () => void;
  driverName: string;
  affectedLoad: string;
  affectedLane: string;
}

export function DisruptionCard({
  disruption,
  result,
  running,
  onRun,
  driverName,
  affectedLoad,
  affectedLane,
}: DisruptionCardProps) {
  return (
    <article className={`disruption-card ${result ? "active" : "incoming"}`}>
      <div className="card-title-row">
        <div><p className="panel-kicker">Operational Exception</p><h3>{result ? "Disruption active" : "Incoming operational disruption"}</h3></div>
        <span className={`badge ${result ? "danger" : "warning"}`}>{result ? "Active" : "Pending"}</span>
      </div>
      <div className="exception-driver">
        <span className="driver-monogram" aria-hidden="true">{driverName.charAt(0)}</span>
        <div><strong>{disruption.driver_id} · {driverName}</strong><span>Customer detention</span></div>
        <b>+{disruption.detention_minutes ?? 0} min</b>
      </div>
      <div className="affected-work"><span>Affected current work</span><strong>{affectedLoad}</strong><small>{affectedLane}</small></div>
      <div className="exception-reason"><span>Reason</span><p>{disruption.reason}</p></div>
      {result && <p className="exception-result"><strong>{result.impacted_assignments.length}</strong> original assignment invalidated</p>}
      {!result && (
        <>
          <button className="button primary full-width" type="button" disabled={running} onClick={onRun}>{running ? "Evaluating plan…" : "Run Re-plan"}</button>
          <p className="helper-text">Evaluate impact while preserving unaffected assignments.</p>
        </>
      )}
      {running && <ul className="evaluation-steps" aria-label="Re-plan activity"><li>Checking current constraints</li><li>Evaluating affected work</li><li>Finding feasible replacements</li><li>Calculating tradeoffs</li></ul>}
    </article>
  );
}
