import { forwardRef, FormEvent } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

const CommandBar = forwardRef<HTMLInputElement, Props>(function CommandBar(
  { value, onChange, onSubmit },
  ref
) {
  function submit(e: FormEvent) {
    e.preventDefault();
    onSubmit();
  }

  return (
    <div className="od-command">
      <form onSubmit={submit}>
        <input
          ref={ref}
          id="od-command-input"
          className="od-command-bar"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="What should get done?"
          aria-label="What should get done?"
        />
      </form>
      <p className="od-command-help">State an outcome. Desk will plan and act.</p>
    </div>
  );
});

export default CommandBar;
