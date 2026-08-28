/** Scroll reveal. Independent of app state. Observes [data-reveal]. */

export function initReveal() {
  if (typeof window === "undefined") return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll("[data-reveal]").forEach((el) => {
      el.classList.add("is-visible");
    });
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  const bind = () => {
    document.querySelectorAll("[data-reveal]:not([data-bound])").forEach((el) => {
      el.setAttribute("data-bound", "1");
      observer.observe(el);
    });
  };

  bind();
  const mo = new MutationObserver(bind);
  mo.observe(document.body, { childList: true, subtree: true });
}
