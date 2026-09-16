import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "default" | "secondary" | "ghost" | "destructive";
type ButtonSize = "default" | "sm" | "icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({ className = "", variant = "default", size = "default", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`ui-button ui-button-${variant} ui-button-${size} ${className}`.trim()} {...props} />;
}