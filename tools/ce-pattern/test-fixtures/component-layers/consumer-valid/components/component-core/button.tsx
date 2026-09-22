import type { ComponentProps } from "react";

import { cn } from "@fixture/components/lib/utils";

export type ButtonProps = ComponentProps<"button">;

export const buttonVariants = (variant: string): string =>
  cn("button", variant);

export function Button(props: ButtonProps) {
  return <button {...props} />;
}
