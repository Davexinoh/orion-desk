export type SessionUser = {
  userId: string;
  displayName: string;
  email: string | null;
  telegramId: string | null;
  telegramUsername: string | null;
};

export const DEV_USER: SessionUser = {
  userId: "dev-demo",
  displayName: "Demo",
  email: null,
  telegramId: null,
  telegramUsername: null,
};

const DEV_COOKIE = "desk_session_dev";
const LEGACY_COOKIE = "desk_session";
const MAX_AGE = 30 * 24 * 60 * 60;

function encode(user: SessionUser): string {
  return encodeURIComponent(JSON.stringify(user));
}

function decode(raw: string): SessionUser | null {
  try {
    const data = JSON.parse(decodeURIComponent(raw)) as SessionUser;
    if (!data || typeof data.userId !== "string" || typeof data.displayName !== "string") {
      return null;
    }
    return {
      userId: data.userId,
      displayName: data.displayName,
      email: data.email ?? null,
      telegramId: data.telegramId ?? null,
      telegramUsername: data.telegramUsername ?? null,
    };
  } catch {
    return null;
  }
}

function readCookie(name: string): string | null {
  const parts = document.cookie.split("; ");
  for (const part of parts) {
    const eq = part.indexOf("=");
    if (eq === -1) continue;
    if (part.slice(0, eq) === name) return part.slice(eq + 1);
  }
  return null;
}

function expireCookie(name: string): void {
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

/** Drop the step-2 JSON desk_session so it cannot collide with the httpOnly cookie. */
export function dropLegacyClientSession(): void {
  const raw = readCookie(LEGACY_COOKIE);
  if (!raw) return;
  if (raw.includes("%7B") || raw.startsWith("{") || raw.includes('"userId"')) {
    expireCookie(LEGACY_COOKIE);
  }
}

/** DEV ONLY fallback when the API is down. Production session is httpOnly desk_session. */
export function getDevSession(): SessionUser | null {
  dropLegacyClientSession();
  const raw = readCookie(DEV_COOKIE);
  if (!raw) return null;
  return decode(raw);
}

export async function fetchServerUser(): Promise<SessionUser | null> {
  try {
    const res = await fetch("/auth/me", { credentials: "include" });
    if (!res.ok) return null;
    const data = (await res.json()) as { user?: SessionUser };
    return data.user ?? null;
  } catch {
    return null;
  }
}

/** DEV ONLY: writable from Vite 5173. Not used on the Telegram production path. */
export function setDevSession(user: SessionUser): void {
  dropLegacyClientSession();
  document.cookie = `${DEV_COOKIE}=${encode(user)}; Path=/; Max-Age=${MAX_AGE}; SameSite=Lax`;
}

export function clearDevSession(): void {
  dropLegacyClientSession();
  expireCookie(DEV_COOKIE);
}

export function isPublicPath(pathname: string): boolean {
  const path = pathname.replace(/\/+$/, "") || "/";
  if (path === "/" || path === "/sign-in") return true;
  if (path === "/desk/m/acme-0491") return true;
  if (path === "/desk/telegram") return true;
  return false;
}

export function safeNext(next: string | null | undefined): string {
  if (!next) return "/desk";
  if (!next.startsWith("/desk")) return "/desk";
  if (next.startsWith("//") || next.includes("://")) return "/desk";
  return next;
}
