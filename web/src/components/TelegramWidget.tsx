import { useEffect, useRef, useState } from "react";

export type TelegramAuthPayload = {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
};

type Props = {
  onAuth: (payload: TelegramAuthPayload) => void;
  onFail?: () => void;
};

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramAuthPayload) => void;
  }
}

export default function TelegramWidget({ onAuth, onFail }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const onAuthRef = useRef(onAuth);
  const [bot, setBot] = useState<string | null | undefined>(undefined);
  onAuthRef.current = onAuth;

  useEffect(() => {
    let cancelled = false;
    fetch("/auth/config", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { telegramBot?: string | null } | null) => {
        if (!cancelled) setBot(data?.telegramBot ?? null);
      })
      .catch(() => {
        if (!cancelled) setBot(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!bot || !host.current) return;
    window.onTelegramAuth = (user) => onAuthRef.current(user);
    host.current.innerHTML = "";
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", bot);
    script.setAttribute("data-size", "medium");
    script.setAttribute("data-radius", "6");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    host.current.appendChild(script);
    return () => {
      window.onTelegramAuth = undefined;
    };
  }, [bot]);

  if (bot === undefined) return <p className="od-signin-sub"> </p>;
  if (!bot) {
    return (
      <button type="button" className="od-btn od-btn-do od-signin-full" onClick={onFail}>
        Continue with Telegram
      </button>
    );
  }

  return (
    <div>
      <p className="od-signin-sub">Continue with Telegram</p>
      <div ref={host} className="od-tg-widget" />
    </div>
  );
}
