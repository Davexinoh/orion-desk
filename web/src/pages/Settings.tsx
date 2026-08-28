import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";
import TelegramWidget, { type TelegramAuthPayload } from "../components/TelegramWidget";
import type { BoardOutlet } from "../components/AppShell";
import { useAuth } from "../lib/AuthContext";

type IntegrationRow = {
  connected?: boolean;
  keyPresent?: boolean;
  mode: "live" | "mock";
};

type Integrations = {
  gmail: IntegrationRow;
  calendar: IntegrationRow;
  drive: IntegrationRow;
  tavily: IntegrationRow;
  llm: IntegrationRow;
};

export default function Settings() {
  const { resetDemo } = useOutletContext<BoardOutlet>();
  const { user, refresh, saveDisplayName, signOut } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.displayName ?? "You");
  const [tgError, setTgError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailDraft, setEmailDraft] = useState("");
  const [emailStep, setEmailStep] = useState<"idle" | "form" | "sent">("idle");
  const [emailWait, setEmailWait] = useState(0);
  const [emailDevLink, setEmailDevLink] = useState<string | null>(null);
  const [policy, setPolicy] = useState<"all" | "external">("all");
  const [confirmClear, setConfirmClear] = useState(false);
  const [integrations, setIntegrations] = useState<Integrations | null>(null);

  useEffect(() => {
    if (user?.displayName) setName(user.displayName);
  }, [user?.displayName]);

  const loadIntegrations = useCallback(() => {
    return fetch("/integrations", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: Integrations | null) => {
        if (data) setIntegrations(data);
      })
      .catch(() => {
        /* keep last */
      });
  }, []);

  useEffect(() => {
    void loadIntegrations();
  }, [loadIntegrations]);

  async function disconnectGoogle() {
    await fetch("/auth/google/disconnect", { method: "POST", credentials: "include" });
    await loadIntegrations();
  }

  const telegramLinked = Boolean(user?.telegramId);

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
          setTgError("Telegram login failed.");
          return;
        }
        await refresh();
      } catch {
        setTgError("Telegram login failed.");
      }
    },
    [refresh]
  );

  useEffect(() => {
    if (emailWait <= 0) return;
    const t = window.setTimeout(() => setEmailWait((w) => w - 1), 1000);
    return () => window.clearTimeout(t);
  }, [emailWait]);

  async function startEmail(e?: FormEvent) {
    e?.preventDefault();
    const normalized = emailDraft.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized)) {
      setEmailError("Enter a valid email.");
      return;
    }
    setEmailError(null);
    setEmailDraft(normalized);
    try {
      const res = await fetch("/auth/email/start", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalized, next: "/desk/settings" }),
      });
      const data = (await res.json().catch(() => ({}))) as { devLink?: string };
      if (res.status === 400) {
        setEmailError("Enter a valid email.");
        return;
      }
      if (!res.ok) {
        setEmailError("Could not send the link.");
        return;
      }
      setEmailWait(60);
      setEmailStep("sent");
      const host = window.location.hostname;
      const local = host === "127.0.0.1" || host === "localhost";
      setEmailDevLink(local && typeof data.devLink === "string" ? data.devLink : null);
    } catch {
      setEmailError("Could not send the link.");
    }
  }

  useEffect(() => {
    function onEsc() {
      setConfirmClear(false);
    }
    window.addEventListener("od-escape", onEsc);
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setConfirmClear(false);
    }
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("od-escape", onEsc);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div className="od-settings">
      <h1 className="od-page-title">Settings</h1>

      <section className="od-settings-section">
        <h2>Profile</h2>
        <label className="od-settings-field">
          Display name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => void saveDisplayName(name)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.currentTarget.blur();
              }
            }}
          />
        </label>
        <div className="od-settings-field">
          Email
          {user?.email ? (
            <span>{user.email}</span>
          ) : emailStep === "idle" ? (
            <button type="button" className="od-btn od-btn-ghost" onClick={() => setEmailStep("form")}>
              Add email
            </button>
          ) : emailStep === "form" ? (
            <form onSubmit={(e) => void startEmail(e)}>
              <input
                type="email"
                autoComplete="email"
                value={emailDraft}
                onChange={(e) => setEmailDraft(e.target.value)}
                autoFocus
              />
              {emailError ? <p className="od-signin-error">{emailError}</p> : null}
              <button type="submit" className="od-btn od-btn-do">
                Send link
              </button>
            </form>
          ) : (
            <div>
              <p>
                Link sent to {emailDraft}
                <br />
                Open it on this device.
              </p>
              {emailError ? <p className="od-signin-error">{emailError}</p> : null}
              {emailDevLink ? (
                <a className="od-signin-text" href={emailDevLink}>
                  Open this desk
                </a>
              ) : null}
              <button
                type="button"
                className="od-btn od-btn-ghost"
                disabled={emailWait > 0}
                onClick={() => void startEmail()}
              >
                {emailWait > 0 ? `Resend in ${emailWait}s` : "Send link"}
              </button>
            </div>
          )}
        </div>
      </section>

      <section className="od-settings-section">
        <h2>Connected tools</h2>
        <ul className="od-tool-rows">
          <li>
            <span>Gmail</span>
            <span className="od-tool-state">
              {integrations?.gmail.connected ? (
                <>
                  Connected
                  {" · "}
                  <button type="button" className="od-btn od-btn-ghost" onClick={() => void disconnectGoogle()}>
                    Disconnect
                  </button>
                </>
              ) : (
                <a href="/auth/google/start">Connect</a>
              )}
            </span>
          </li>
          <li>
            <span>Calendar</span>
            <span className="od-tool-state">
              {integrations?.calendar.connected ? (
                <>
                  Connected
                  {" · "}
                  <button type="button" className="od-btn od-btn-ghost" onClick={() => void disconnectGoogle()}>
                    Disconnect
                  </button>
                </>
              ) : (
                <a href="/auth/google/start">Connect</a>
              )}
            </span>
          </li>
          <li>
            <span>Drive</span>
            <span className="od-tool-state">
              {integrations?.drive.connected ? (
                <>
                  Connected
                  {" · "}
                  <button type="button" className="od-btn od-btn-ghost" onClick={() => void disconnectGoogle()}>
                    Disconnect
                  </button>
                </>
              ) : (
                <a href="/auth/google/start">Connect</a>
              )}
            </span>
          </li>
          <li>
            <span>Web search</span>
            <span className="od-tool-state">
              {integrations?.tavily.keyPresent ? "Key present" : "Key absent"}
            </span>
          </li>
          <li>
            <span>LLM</span>
            <span className="od-tool-state">
              {integrations?.llm.keyPresent ? "Key present" : "Key absent"}
            </span>
          </li>
          <li>
            <span>Notion</span>
            <span className="od-tool-state">Coming soon</span>
          </li>
          <li>
            <span>Telegram</span>
            <span className="od-tool-state">
              {telegramLinked ? (
                <>
                  {user?.telegramUsername ? `Linked as @${user.telegramUsername}` : "Linked"}
                  {" · "}
                  <Link to="/desk/telegram">Preview templates</Link>
                </>
              ) : (
                <>
                  Link Telegram
                  {" · "}
                  <Link to="/desk/telegram">Preview templates</Link>
                </>
              )}
            </span>
          </li>
          {!telegramLinked ? (
            <li>
              <TelegramWidget
                onAuth={onTelegram}
                onFail={() => setTgError("Telegram login failed.")}
              />
            </li>
          ) : null}
          {tgError ? <li className="od-signin-error">{tgError}</li> : null}
        </ul>
      </section>

      <section className="od-settings-section">
        <h2>Approval policy</h2>
        <label className="od-radio">
          <input
            type="radio"
            name="policy"
            checked={policy === "all"}
            onChange={() => setPolicy("all")}
          />
          Confirm all external sends and calendar writes
        </label>
        <label className="od-radio">
          <input
            type="radio"
            name="policy"
            checked={policy === "external"}
            onChange={() => setPolicy("external")}
          />
          Confirm external sends only
        </label>
      </section>

      <section className="od-settings-section">
        <h2>Session</h2>
        <button
          type="button"
          className="od-btn od-btn-ghost"
          onClick={async () => {
            await signOut();
            navigate("/");
          }}
        >
          Sign out
        </button>
      </section>

      <section className="od-settings-section od-danger">
        <h2>Danger zone</h2>
        <p className="od-settings-note">Clear local demo state. Resets board and approvals to seed.</p>
        {confirmClear ? (
          <div className="od-danger-confirm">
            <button
              type="button"
              className="od-btn od-btn-do"
              onClick={() => {
                resetDemo();
                setConfirmClear(false);
              }}
            >
              Confirm
            </button>
            <button type="button" className="od-btn od-btn-ghost" onClick={() => setConfirmClear(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <button type="button" className="od-btn od-btn-ghost" onClick={() => setConfirmClear(true)}>
            Clear local demo state
          </button>
        )}
      </section>
    </div>
  );
}
