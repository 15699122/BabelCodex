import type { HTMLAttributes } from "react";

type SurfaceProps = HTMLAttributes<HTMLElement>;

export function Card({ className = "", ...props }: SurfaceProps) {
  return <section className={`ui-card ${className}`.trim()} {...props} />;
}

export function CardHeader({ className = "", ...props }: SurfaceProps) {
  return <div className={`ui-card-header ${className}`.trim()} {...props} />;
}

export function CardContent({ className = "", ...props }: SurfaceProps) {
  return <div className={`ui-card-content ${className}`.trim()} {...props} />;
}