import {
  Button,
  buttonVariants,
  type ButtonProps,
} from "../component-core/button";

export type NavLinkProps = ButtonProps & { href: string };

export const navLinkVariants = (variant: string): string =>
  buttonVariants(`nav-${variant}`);

export function NavLink(props: NavLinkProps) {
  return <Button {...props} />;
}
