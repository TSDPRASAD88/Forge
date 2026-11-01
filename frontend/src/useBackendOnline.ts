import { useEffect, useState } from "react";

/** Polls /api/health. Returns false when the backend cannot be reached. */
export function useBackendOnline(intervalMs = 15000): boolean {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const res = await fetch("/api/health");
        if (!cancelled) setOnline(res.ok);
      } catch {
        if (!cancelled) setOnline(false);
      }
    }
    check();
    const id = setInterval(check, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  return online;
}