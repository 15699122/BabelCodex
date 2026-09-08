import type { HTMLAttributes } from "react";

export function Progress({ value, className = "", ...props }: HTMLAttributes<HTMLDivElement> & { value: number }) {
  const boundedValue = Math.min(100, Math.max(0, value));
  return (
    <div className={`ui-progress ${className}`.trim()} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={boundedValue} {...props}>
      <span style={{ width: `${boundedValue}%` }} />
    </div>
  );
}