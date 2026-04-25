import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonProps = {
  children: ReactNode;
  href?: string;
} & ButtonHTMLAttributes<HTMLButtonElement> &
  AnchorHTMLAttributes<HTMLAnchorElement>;

export default function Button({ children, href, ...props }: ButtonProps) {
  if (href) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  }

  return <button type="button" {...props}>{children}</button>;
}
