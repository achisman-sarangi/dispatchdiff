import type { AssignmentChange, Load } from "../api/types";
import { formatDateTime, routeLabel } from "../utils/format";

export function AssignmentChangeCard({ change, load }: { change: AssignmentChange; load?: Load }) {
  const assignment = change.proposed_assignment ?? change.previous_assignment;
  return (
    <article className={`change-card ${change.change_type.toLowerCase()}`}>
      <div className="change-card-header">
        <strong>{change.driver_id} <span aria-hidden="true">→</span> {change.load_id}</strong>
        <span className={`badge change-${change.change_type.toLowerCase()}`}>{change.change_type}</span>
      </div>
      {load && <p className="route">{routeLabel(load.origin_city, load.origin_state, load.destination_city, load.destination_state)}</p>}
      {assignment && change.change_type !== "PRESERVED" && (
        <dl className="change-schedule">
          <div><dt>Pickup</dt><dd>{formatDateTime(assignment.planned_pickup_at)}</dd></div>
          <div><dt>Delivery</dt><dd>{formatDateTime(assignment.planned_delivery_at)}</dd></div>
          <div><dt>Deadhead</dt><dd>{assignment.deadhead_minutes} min</dd></div>
          <div><dt>Score</dt><dd>{assignment.score.toFixed(2)}</dd></div>
        </dl>
      )}
      {change.reason_codes.length > 0 && <p className="reason-code">{change.reason_codes.join(", ")}</p>}
      <p className="change-explanation">{change.explanation}</p>
    </article>
  );
}
