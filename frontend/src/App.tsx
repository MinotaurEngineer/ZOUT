import { useState } from "react";
import { Button, Container, Typography } from "@mui/material";
import { ApiError, getSummary, logout } from "./api";
import Login from "./Login";
import type { Summary } from "./types";

import Dashboard from "./Dashboard";

export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null);

  async function load() {
    try {
      setSummary(await getSummary());
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        logout();
        setSummary(null);
      } else throw e;
    }
  }

  if (!summary) return <Login onLoggedIn={load} />;

  return (
    <Container>
      <Typography variant="h5">{summary.tenant.name}</Typography>
      <Button onClick={() => { logout(); setSummary(null); }}>Sign out</Button>
      <Dashboard summary={summary} />
    </Container>
  );
}