export interface TimelineEvent {
  label: string;
  detail: string;
}

export function EventTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <details className="timeline-panel" open>
      <summary><span><span className="panel-kicker">Activity</span><strong>Decision log</strong></span><small>{events.length} events</small></summary>
      <ol className="timeline">{events.map((event, index) => <li key={`${event.label}-${index}`}><span className="timeline-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{event.label}</strong><p>{event.detail}</p></div></li>)}</ol>
    </details>
  );
}
