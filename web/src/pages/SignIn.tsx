import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import TelegramWidget, { type TelegramAuthPayload } from "../components/TelegramWidget";
import { useAuth } from "../lib/AuthContext";
import { safeNext } from "../lib/session";
import "../styles/signin.css";

type Step = "choose" | "email" | "sent";

function validEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim().toLowerCase());
}

function isLocalApp(): boolean {
  const host = window.location.hostname;
  return host === "127.0.0.1" || host === "localhost";
}

export default function SignIn() {
  const { user, ready, signInDev, refresh } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeNext(params.get("next"));
  const showDev = params.get("dev") === "1";
  const [step, setStep] = useState<Step>("choose");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [wait, setWait] = useState(0);
  const [devLink, setDevLink] = useState<string | null>(null);

  useEffect(() => {
    if (wait <= 0) return;
    const t = window.setTimeout(() => setWait((w) => w - 1), 1000);
    return () => window.clearTimeout(t);
  }, [wait]);

  const onTelegram = useCallback(
    async (payload: TelegramAuthPayload) => {
      try {
        const res = await fetch("/auth/telegram", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          setError("Telegram login failed.");
          return;
        }
        await refresh();
        navigate(next);
      } catch {
        setError("Telegram login failed.");
      }
    },
    [navigate, next, refresh]
  );

  async function send(e?: FormEvent) {
    e?.preventDefault();
    const normalized = email.trim().toLowerCase();
    if (!validEmail(normalized)) {
      setError("Enter a valid email.");
      return;
    }
    setError(null);
    setEmail(normalized);
    try {
      const res = await fetch("/auth/email/start", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalized, next }),
      });
      const data = (await res.json().catch(() => ({}))) as { detail?: string; devLink?: string };
      if (res.status === 400) {
        setError("Enter a valid email.");
        return;
      }
      if (!res.ok) {
        setError("Could not send the link.");
        return;
      }
      setWait(60);
      setStep("sent");
      const link = typeof data.devLink === "string" ? data.devLink : null;
      setDevLink(isLocalApp() && link ? link : null);
    } catch {
      setError("Could not send the link.");
    }
  }

  if (!ready) return null;
  if (user) return <Navigate to={next} replace />;

  return (
    <div className="od-signin">
      <div className="od-signin-card">
        <p className="od-signin-mark">
          Orion <span>Desk</span>
        </p>
        <h1>This desk is yours.</h1>
        <p className="od-signin-sub">Telegram first. Email if you need it.</p>

        {step === "choose" ? (
          <div className="od-signin-actions">
            <TelegramWidget
              onAuth={onTelegram}
              onFail={() => setError("Telegram login failed.")}
            />
            {error ? <p className="od-signin-error">{error}</p> : null}
            {showDev ? (
              <button
                type="button"
                className="od-btn od-btn-ghost od-signin-full"
                onClick={async () => {
                  await signInDev();
                  navigate(next);
                }}
              >
                Sign in as demo
              </button>
            ) : null}
            <button
              type="button"
              className="od-btn od-btn-ghost od-signin-full"
              onClick={() => {
                setError(null);
                setStep("email");
              }}
            >
              Email a link
            </button>
            <Link className="od-signin-text" to="/desk/m/acme-0491">
              Watch the Acme demo
            </Link>
          </div>
        ) : null}

        {step === "email" ? (
          <form className="od-signin-actions" onSubmit={(e) => void send(e)}>
            <label className="od-signin-field">
              Email a link
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
            </label>
            {error ? <p className="od-signin-error">{error}</p> : null}
            <button type="submit" className="od-btn od-btn-do od-signin-full">
              Send link
            </button>
            <button
              type="button"
              className="od-btn od-btn-ghost od-signin-full"
              onClick={() => {
                setError(null);
                setDevLink(null);
                setStep("choose");
              }}
            >
              Use Telegram instead
            </button>
          </form>
        ) : null}

        {step === "sent" ? (
          <div className="od-signin-actions">
            <p>
              Link sent to {email}
              <br />
              Open it on this device.
            </p>
            {error ? <p className="od-signin-error">{error}</p> : null}
            {devLink ? (
              <a className="od-signin-text" href={devLink}>
                Open this desk
              </a>
            ) : null}
            <button
              type="button"
              className="od-btn od-btn-ghost od-signin-full"
              disabled={wait > 0}
              onClick={() => void send()}
            >
              {wait > 0 ? `Resend in ${wait}s` : "Send link"}
            </button>
            <button
              type="button"
              className="od-btn od-btn-ghost od-signin-full"
              onClick={() => {
                setError(null);
                setDevLink(null);
                setStep("choose");
              }}
            >
              Use Telegram instead
            </button>
          </div>
        ) : null}

        <p className="od-signin-legal">Desk does not send external messages without approval.</p>
      </div>
    </div>
  );
}
