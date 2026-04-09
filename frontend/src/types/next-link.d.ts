declare module 'next/link' {
  import type { AnchorHTMLAttributes, DetailedHTMLProps, ReactNode } from 'react';

  export type LinkProps = DetailedHTMLProps<
    AnchorHTMLAttributes<HTMLAnchorElement>,
    HTMLAnchorElement
  > & {
    href: string;
    size?: string;
    children?: ReactNode;
  };

  export default function Link(props: LinkProps): ReactNode;
}
