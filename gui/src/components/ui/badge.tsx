import type { HTMLAttributes } from "react";

type BadgeVariant = "default" | "success" | "warning" | "muted" | "destructive";

export function Badge({ className = "", variant = "default", ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return <span className={`ui-badge ui-badge-${variant} ${className}`.trim()} {...props} />;
}