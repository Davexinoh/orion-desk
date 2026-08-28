import { useEffect } from "react";
import type { Receipt } from "../lib/types";
import ActionReceipt from "./ActionReceipt";

type Props = {
  open: boolean;
  receipt: Receipt | null;
  onClose: () => void;
  onDoIt?: () => void;
  onKeep?: () => void;
};

export default function ReceiptDrawer({
  open,
  receipt,
  onClose,
  onDoIt,
  onKeep,
}: Props) {
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !receipt) return null;

  return (
    <div className="od-drawer-root">
      <button
        type="button"
        className="od-drawer-overlay"
        aria-label="Close receipt"
        onClick={onClose}
      />
      <aside className="od-drawer" role="dialog" aria-modal="false" aria-label="Action receipt">
        <button type="button" className="od-drawer-x" onClick={onClose} aria-label="Close">
          ×
        </button>
        <button
          type="button"
          className="od-btn od-btn-ghost od-print"
          onClick={() => window.print()}
        >
          Print
        </button>
        <ActionReceipt
          receipt={receipt}
          onApprove={onDoIt ? () => onDoIt() : undefined}
          onDecline={onKeep ? () => onKeep() : undefined}
        />
      </aside>
    </div>
  );
}
