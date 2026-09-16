export function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatMinutes(value: number): string {
  return `${value.toLocaleString("en-US")} min`;
}

export function formatSigned(
  value: number,
  formatter: (absoluteValue: number) => string = String,
): string {
  if (value === 0) return "No change";
  return `${value > 0 ? "+" : "−"}${formatter(Math.abs(value))}`;
}

export function routeLabel(
  originCity: string,
  originState: string,
  destinationCity: string,
  destinationState: string,
): string {
  return `${originCity}, ${originState} → ${destinationCity}, ${destinationState}`;
}
