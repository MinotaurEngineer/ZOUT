import { useState } from "react";
import type { FormEvent } from "react";
import { Alert, Button, Container, Stack, TextField, Typography } from "@mui/material";
import { ApiError, login } from "./api";

export default function Login({ onLoggedIn }: { onLoggedIn: () => Promise<void> }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      await onLoggedIn();
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? "Invalid email or password" : "Something went wrong");
    }
  }

  return (
    <Container maxWidth="xs">
      <Stack component="form" spacing={2} onSubmit={submit} sx={{ mt: 8 }}>
        <Typography variant="h5">Sign in</Typography>
        {error && <Alert severity="error">{error}</Alert>}
        <TextField label="Email" value={username} onChange={(e) => setUsername(e.target.value)} />
        <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <Button type="submit" variant="contained">Sign in</Button>
      </Stack>
    </Container>
  );
}