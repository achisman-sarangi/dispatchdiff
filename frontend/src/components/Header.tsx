interface HeaderProps {
  apiOnline: boolean;
  onReset: () => void;
}

export function Header({ apiOnline, onReset }: HeaderProps) {
  return (
    <header className="topbar">
      <div className="workspace-identity"><p>Fleet Operations</p><span>/</span><strong>Southeast Demo</strong></div>
      <div className="header-actions">
        <span className="topbar-chip">Demo Environment</span>
        <span className="plan-status"><span aria-hidden="true">✓</span> Plan healthy</span>
        <span className={`api-status ${apiOnline ? "online" : "offline"}`}>
          <span aria-hidden="true" className="status-dot" />
          {apiOnline ? "Connected" : "Unavailable"}
        </span>
        <button className="button secondary" type="button" onClick={onReset}>
          Reset Demo
        </button>
      </div>
    </header>
  );
}
