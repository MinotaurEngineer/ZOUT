import type { Summary } from "./types";

let token: string | null = null; // in memory only

export class ApiError extends Error {
  status: number;
  constructor(status: number) {
    super(`HTTP ${status}`);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!res.ok) throw new ApiError(res.status);
  return res.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<void> {
  const data = await request<{ access: string }>("/api/token/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  token = data.access;
}

export const logout = () => {
  token = null;
};

export const getSummary = () => request<Summary>("/api/dashboard/summary/");