interface SidebarProps {
  drivers: number;
  loads: number;
  apiOnline: boolean;
}

export function Sidebar({ drivers, loads, apiOnline }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark" aria-hidden="true">D</div>
        <div><h1>DispatchDiff</h1><p>Fleet Operations</p></div>
      </div>
      <nav aria-label="Workspace navigation">
        <a className="nav-item selected" href="#overview"><span aria-hidden="true">⌂</span>Overview</a>
        <a className="nav-item" href="#fleet-plan"><span aria-hidden="true">≡</span>Fleet Plan</a>
        <a className="nav-item" href="#exceptions"><span aria-hidden="true">!</span>Exceptions</a>
        <a className="nav-item" href="#decision-log"><span aria-hidden="true">✓</span>Decision Log</a>
      </nav>
      <div className="environment-card">
        <p className="sidebar-label">Demo Environment</p>
        <div className="environment-stats"><span><strong>{drivers}</strong> Drivers</span><span><strong>{loads}</strong> Loads</span></div>
        <p className="service-status"><span className={apiOnline ? "online" : "offline"} aria-hidden="true" />Planning service {apiOnline ? "online" : "offline"}</p>
      </div>
    </aside>
  );
}
