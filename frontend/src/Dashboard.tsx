import {
  Card, CardContent, Chip, Grid, Stack, Table, TableBody, TableCell,
  TableHead, TableRow, Typography,
} from "@mui/material";
import { dateTime, money, percent } from "./format";
import type { Summary } from "./types";

function Stat({ label, value, color }: { label: string; value: string | number; color?: "error.main" }) {
  return (
    <Card>
      <CardContent>
        <Typography color="text.secondary">{label}</Typography>
        <Typography variant="h4" color={color}>{value}</Typography>
      </CardContent>
    </Card>
  );
}

export default function Dashboard({ summary }: { summary: Summary }) {
  const t = summary.tenant;
  return (
    <Stack spacing={3}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Stat label="Repeat guests" value={percent(summary.repeat_guest_rate, t)} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Stat
            label="Failed webhooks"
            value={summary.failed_webhook_count}
            color={summary.failed_webhook_count > 0 ? "error.main" : undefined}
          />
        </Grid>
      </Grid>

      <Stack direction="row" spacing={1}>
        {Object.entries(summary.shipment_status_counts).map(([status, n]) => (
          <Chip key={status} label={`${status.replace("_", " ")}: ${n}`} />
        ))}
      </Stack>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Placed</TableCell>
            <TableCell>Guest</TableCell>
            <TableCell align="right">Total</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Shipment</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {summary.recent_orders.map((o) => (
            <TableRow key={o.id}>
              <TableCell>{dateTime(o.created_at, t)}</TableCell>
              <TableCell>{o.customer_ref}</TableCell>
              <TableCell align="right">{money(o.total_cents, t)}</TableCell>
              <TableCell>{o.status}</TableCell>
              <TableCell>{o.shipment_status ? <Chip size="small" label={o.shipment_status.replace("_", " ")} /> : "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Stack>
  );
}