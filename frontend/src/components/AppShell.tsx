import type { ReactNode } from "react";

import { Sidebar } from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
  drivers: number;
  loads: number;
  apiOnline: boolean;
}

export function AppShell({ children, drivers, loads, apiOnline }: AppShellProps) {
  return <div className="app-shell"><Sidebar drivers={drivers} loads={loads} apiOnline={apiOnline} />{children}</div>;
}
