import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Dashboard from "./Dashboard";
import type { Summary } from "./types";

const summary: Summary = {
  tenant: { name: "Test", locale: "es-AR", currency: "ARS", timezone: "America/Argentina/Buenos_Aires" },
  recent_orders: [],
  repeat_guest_rate: 0.4,
  failed_webhook_count: 7,
  shipment_status_counts: { pending: 1, in_transit: 2, delivered: 3 },
};

test("shows the failed webhook count", () => {
  render(<Dashboard summary={summary} />);
  expect(screen.getByText("Failed webhooks")).toBeTruthy();
  expect(screen.getByText("7")).toBeTruthy();
});