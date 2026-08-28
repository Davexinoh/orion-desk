type Props = {
  label: string;
  onDoIt: () => void;
  onKeep: () => void;
};

export default function ApprovalBar({ label, onDoIt, onKeep }: Props) {
  return (
    <div className="od-approval-bar">
      <p className="od-approval-bar-label">{label}</p>
      <div className="od-approval-bar-actions">
        <button type="button" className="od-btn od-btn-ghost" onClick={onKeep}>
          Keep as draft
        </button>
        <button type="button" className="od-btn od-btn-do" onClick={onDoIt}>
          Do it
        </button>
      </div>
    </div>
  );
}
