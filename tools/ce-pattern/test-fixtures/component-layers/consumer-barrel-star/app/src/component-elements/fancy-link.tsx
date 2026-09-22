import { NavLink, type NavLinkProps } from "@fixture/components";

export type FancyLinkProps = NavLinkProps;

export function FancyLink(props: FancyLinkProps) {
  return <NavLink {...props} />;
}
