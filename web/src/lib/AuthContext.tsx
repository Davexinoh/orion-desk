import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  clearDevSession,
  DEV_USER,
  dropLegacyClientSession,
  fetchServerUser,
  getDevSession,
  setDevSession,
  type SessionUser,
} from "./session";

type Auth = {
  user: SessionUser | null;
  ready: boolean;
  refresh: () => Promise<void>;
  saveDisplayName: (displayName: string) => Promise<void>;
  signInDev: () => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async () => {
    dropLegacyClientSession();
    const server = await fetchServerUser();
    setUser(server ?? getDevSession());
  }, []);

  useEffect(() => {
    void refresh().finally(() => setReady(true));
  }, [refresh]);

  const value = useMemo<Auth>(
    () => ({
      user,
      ready,
      refresh,
      saveDisplayName: async (displayName: string) => {
        const cleaned = displayName.trim();
        if (!cleaned) return;
        try {
          const res = await fetch("/auth/profile", {
            method: "PATCH",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ displayName: cleaned }),
          });
          if (res.ok) {
            const data = (await res.json()) as { user?: SessionUser };
            if (data.user) {
              setUser(data.user);
              return;
            }
          }
        } catch {
          /* API down */
        }
        const server = await fetchServerUser();
        if (server) return;
        setUser((prev) => {
          if (!prev) return prev;
          const next = { ...prev, displayName: cleaned };
          setDevSession(next);
          return next;
        });
      },
      signInDev: async () => {
        try {
          const res = await fetch("/auth/dev", { method: "POST", credentials: "include" });
          if (res.ok) {
            const data = (await res.json()) as { user?: SessionUser };
            if (data.user) {
              clearDevSession();
              setUser(data.user);
              return;
            }
          }
        } catch {
          /* API down — local demo cookie only */
        }
        setDevSession(DEV_USER);
        setUser(DEV_USER);
      },
      signOut: async () => {
        try {
          await fetch("/auth/logout", { method: "POST", credentials: "include" });
        } catch {
          /* server may be down */
        }
        clearDevSession();
        setUser(null);
      },
    }),
    [user, ready, refresh]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): Auth {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
