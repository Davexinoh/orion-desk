import { MouseEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

const LINKS = [
  { href: "#product", label: "Product" },
  { href: "#receipt", label: "Receipts" },
  { href: "#demo", label: "Demo" },
  { href: "https://github.com/Davexinoh/orion-desk", label: "GitHub", external: true },
] as const;

type Marker = { x: number; w: number };

export default function StudioNav() {
  const { user } = useAuth();
  const list = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState("#product");
  const [marker, setMarker] = useState<Marker>({ x: 0, w: 0 });
  const [pressed, setPressed] = useState<string | null>(null);

  function place(el: HTMLElement | null) {
    const row = list.current;
    if (!row || !el) return;
    const a = row.getBoundingClientRect();
    const b = el.getBoundingClientRect();
    setMarker({ x: b.left - a.left, w: b.width });
  }

  useEffect(() => {
    const ids = ["product", "receipt", "demo"];
    const nodes = ids
      .map((id) => document.getElementById(id))
      .filter((n): n is HTMLElement => Boolean(n));
    if (!nodes.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        const vis = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (vis?.target.id) setActive(`#${vis.target.id}`);
      },
      { rootMargin: "-20% 0px -55% 0px", threshold: [0.15, 0.4, 0.7] }
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const row = list.current;
    if (!row) return;
    const el = row.querySelector<HTMLElement>(`[data-href="${active}"]`);
    place(el);
  }, [active]);

  function onEnter(e: MouseEvent<HTMLElement>) {
    place(e.currentTarget);
  }

  function onLeave() {
    const row = list.current;
    const el = row?.querySelector<HTMLElement>(`[data-href="${active}"]`);
    place(el ?? null);
  }

  function goHash(e: MouseEvent<HTMLAnchorElement>, href: string) {
    if (!href.startsWith("#")) return;
    e.preventDefault();
    setPressed(href);
    window.setTimeout(() => setPressed(null), 180);
    const node = document.getElementById(href.slice(1));
    node?.scrollIntoView({ behavior: "smooth", block: "start" });
    setActive(href);
    history.replaceState(null, "", href);
  }

  return (
    <header className="studio-nav">
      <Link
        to="/"
        className="mkt-wordmark studio-nav-mark"
        onClick={(e) => {
          if (window.location.pathname !== "/") return;
          e.preventDefault();
          window.scrollTo({ top: 0, behavior: "smooth" });
          setActive("#product");
        }}
      >
        Orion <span>Desk</span>
      </Link>
      <div className="studio-nav-tray" ref={list} onMouseLeave={onLeave}>
        <span
          className="studio-nav-marker"
          style={{ transform: `translateX(${marker.x}px)`, width: marker.w }}
        />
        {LINKS.map((l) => {
          const current = !("external" in l && l.external) && active === l.href;
          const cls = `studio-nav-link${current ? " is-on" : ""}${pressed === l.href ? " is-press" : ""}`;
          if ("external" in l && l.external) {
            return (
              <a
                key={l.href}
                href={l.href}
                data-href={l.href}
                className={cls}
                target="_blank"
                rel="noreferrer"
                onMouseEnter={onEnter}
              >
                {l.label}
              </a>
            );
          }
          return (
            <a
              key={l.href}
              href={l.href}
              data-href={l.href}
              className={cls}
              onMouseEnter={onEnter}
              onClick={(e) => goHash(e, l.href)}
            >
              {l.label}
            </a>
          );
        })}
      </div>
      {user ? (
        <Link className="studio-nav-in" to="/desk/settings">
          {user.displayName}
        </Link>
      ) : (
        <Link className="studio-nav-in" to="/sign-in">
          Sign in
        </Link>
      )}
    </header>
  );
}
