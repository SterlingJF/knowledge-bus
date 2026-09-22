import { Button, type ButtonProps } from "@fixture/components";

export type LinkButtonProps = ButtonProps & { href: string };

export function LinkButton(props: LinkButtonProps) {
  return <Button {...props} />;
}
