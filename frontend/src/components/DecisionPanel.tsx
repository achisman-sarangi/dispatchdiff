export type DecisionState = "PENDING" | "APPROVED" | "REJECTED";

interface DecisionPanelProps {
  preservedCount: number;
  decision: DecisionState;
  onApprove: () => void;
  onReject: () => void;
}

export function DecisionPanel({ preservedCount, decision, onApprove, onReject }: DecisionPanelProps) {
  return (
    <section className={`decision-panel ${decision.toLowerCase()}`}>
      <div className="decision-copy">
        <p className="panel-kicker">Dispatcher decision</p>
        <h2>{decision === "PENDING" ? "Proposed plan ready" : decision === "APPROVED" ? "Re-plan approved" : "Current plan retained"}</h2>
        <p>{decision === "PENDING" && `The disrupted load remains covered. ${preservedCount} existing assignments preserved.`}{decision === "APPROVED" && "Proposed plan approved in demo. The decision is visible locally only."}{decision === "REJECTED" && "Current plan retained. It still contains the invalidated assignment and requires dispatcher attention."}</p>
        <span className="demo-label">Demo decision · not persisted</span>
      </div>
      {decision === "PENDING" && <div className="decision-actions"><button className="button secondary" type="button" onClick={onReject}>Keep Current Plan</button><button className="button primary" type="button" onClick={onApprove}>Approve Re-plan</button></div>}
    </section>
  );
}
