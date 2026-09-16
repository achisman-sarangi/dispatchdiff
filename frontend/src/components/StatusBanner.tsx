import type { ReactNode } from "react";

export function StatusBanner({
  tone,
  children,
}: {
  tone: "success" | "warning" | "error" | "info";
  children: ReactNode;
}) {
  return (
    <div className={`status-banner ${tone}`} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
