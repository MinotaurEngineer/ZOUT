import type { Summary } from "./types";

type Tenant = Summary["tenant"];

// Money arrives as integer cents; the division by 100 happens here and nowhere else.
export const money = (cents: number, t: Tenant) =>
  new Intl.NumberFormat(t.locale, { style: "currency", currency: t.currency }).format(cents / 100);

export const percent = (ratio: number, t: Tenant) =>
  new Intl.NumberFormat(t.locale, { style: "percent", maximumFractionDigits: 0 }).format(ratio);

// Timestamps arrive in UTC; display converts to the tenant's timezone, not the browser's.
export const dateTime = (iso: string, t: Tenant) =>
  new Intl.DateTimeFormat(t.locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: t.timezone,
  }).format(new Date(iso));