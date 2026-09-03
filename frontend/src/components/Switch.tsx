import type { ReactNode } from "react";

type Props = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: ReactNode;
  disabled?: boolean;
  required?: boolean;
  className?: string;
};

export function Switch({
  checked,
  onChange,
  children,
  disabled,
  required,
  className,
}: Props) {
  return (
    <label className={["ui-switch", className].filter(Boolean).join(" ")}>
      <input
        type="checkbox"
        role="switch"
        className="visually-hidden"
        checked={checked}
        disabled={disabled}
        required={required}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="ui-switch-track" aria-hidden="true" />
      <span className="ui-switch-text">{children}</span>
    </label>
  );
}
