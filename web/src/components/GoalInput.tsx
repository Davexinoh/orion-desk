import { FormEvent, useState } from "react";

type Props = {
  onSubmit: (intent: string) => void;
  placeholder?: string;
  submitLabel?: string;
  autoFocus?: boolean;
  disabled?: boolean;
  initial?: string;
};

export default function GoalInput({
  onSubmit,
  placeholder = "What do you need handled?",
  submitLabel = "Handle it",
  autoFocus,
  disabled,
  initial = "",
}: Props) {
  const [value, setValue] = useState(initial);

  function submit(e: FormEvent) {
    e.preventDefault();
    const intent = value.trim();
    if (!intent || disabled) return;
    onSubmit(intent);
    setValue("");
  }

  return (
    <form className="goal-input" onSubmit={submit}>
      <span className="prompt" aria-hidden="true">
        ▸
      </span>
      <input
        type="text"
        name="intent"
        autoComplete="off"
        autoFocus={autoFocus}
        disabled={disabled}
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Goal"
      />
      <button className="btn btn-accent submit" type="submit" disabled={disabled}>
        {submitLabel}
      </button>
    </form>
  );
}
