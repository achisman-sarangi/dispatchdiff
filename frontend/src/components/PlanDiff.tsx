import type { AssignmentChange, Load, ReplanResult } from "../api/types";
import { formatDateTime, routeLabel } from "../utils/format";

export function PlanDiff({ result, loads }: { result: ReplanResult; loads: Load[] }) {
  const loadsById = new Map(loads.map((load) => [load.id, load]));
  const removed = result.assignment_changes.find((change) => change.change_type === "REMOVED");
  const replacement = result.assignment_changes.find(
    (change) => change.change_type === "ADDED" && change.load_id === removed?.load_id,
  );
  const additional = result.assignment_changes.filter(
    (change) => change.change_type === "ADDED" && change.load_id !== removed?.load_id,
  );
  const preserved = result.assignment_changes.filter((change) => change.change_type === "PRESERVED");

  return (
    <div className="plan-changes">
      <section className="replacement-flow" aria-label="Reassignment flow">
        {removed && <ChangeNode change={removed} load={loadsById.get(removed.load_id)} kind="removed" />}
        <div className="reassignment-connector"><span aria-hidden="true">↓</span><strong>Reassigned to</strong></div>
        {replacement && <ChangeNode change={replacement} load={loadsById.get(replacement.load_id)} kind="replacement" />}
      </section>

      {additional.map((change) => (
        <section className="additional-assignment" key={`${change.driver_id}-${change.load_id}`}>
          <p className="panel-kicker">Additional assignment</p>
          <ChangeNode change={change} load={loadsById.get(change.load_id)} kind="additional" />
        </section>
      ))}

      <section className="preserved-work">
        <div className="preserved-heading"><div><p className="panel-kicker">Preserved work</p><h3>✓ {preserved.length} assignments preserved</h3></div><span>Existing work left exactly as planned</span></div>
        <div className="preserved-strip">{preserved.map((change) => <span key={`${change.driver_id}-${change.load_id}`}><strong>{change.driver_id}</strong> → {change.load_id}</span>)}</div>
        <p className="preserved-explanation">Assignment preserved because it remains feasible and was not affected by the disruption.</p>
      </section>
    </div>
  );
}

function ChangeNode({ change, load, kind }: { change: AssignmentChange; load?: Load; kind: "removed" | "replacement" | "additional" }) {
  const assignment = change.proposed_assignment ?? change.previous_assignment;
  return (
    <article className={`change-node ${kind}`}>
      <header>
        <div><h3 className="panel-kicker">{kind === "removed" ? "REMOVED" : kind === "replacement" ? "REPLACEMENT" : "ADDED"}</h3><h4>{change.driver_id} <span aria-hidden="true">→</span> {change.load_id}</h4></div>
        {kind === "removed" && <span className="badge danger">Infeasible</span>}
        {kind !== "removed" && <span className="badge info">Feasible</span>}
      </header>
      {load && <p className="change-lane">{routeLabel(load.origin_city, load.origin_state, load.destination_city, load.destination_state)}</p>}
      {assignment && <div className="change-meta"><span>Pickup {formatDateTime(assignment.planned_pickup_at)}</span><span>{assignment.deadhead_minutes} min deadhead</span>{kind !== "removed" && <span>Score {assignment.score.toFixed(2)}</span>}</div>}
      {change.reason_codes.length > 0 && <code>{change.reason_codes.join(", ")}</code>}
      <p>{change.explanation}</p>
    </article>
  );
}
