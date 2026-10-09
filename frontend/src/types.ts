export type ShipmentStatus = "pending" | "in_transit" | "delivered";

export interface Order {
  id: number;
  customer_ref: string;
  total_cents: number;
  status: "pending" | "completed";
  shipment_status: ShipmentStatus | null;
  created_at: string;
}

export interface Summary {
  tenant: { name: string; locale: string; currency: string; timezone: string };
  recent_orders: Order[];
  repeat_guest_rate: number;
  failed_webhook_count: number;
  shipment_status_counts: Record<ShipmentStatus, number>;
}