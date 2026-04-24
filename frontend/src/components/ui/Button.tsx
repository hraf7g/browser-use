import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary';

type SharedButtonProps = {
  children: ReactNode;
  className?: string;
  variant?: ButtonVariant;
};

type ButtonAsButtonProps = SharedButtonProps &
  ButtonHTMLAttributes<HTMLButtonElement> & {
    href?: undefined;
  };

type ButtonAsAnchorProps = SharedButtonProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
  };

type ButtonProps = ButtonAsButtonProps | ButtonAsAnchorProps;

function getButtonClassName(variant: ButtonVariant, className?: string) {
  return ['button-base', variant === 'primary' ? 'button-primary' : 'button-secondary', className]
    .filter(Boolean)
    .join(' ');
}

export default function Button(props: ButtonProps) {
  const { children, className, variant = 'primary' } = props;
  const buttonClassName = getButtonClassName(variant, className);

  if ('href' in props && props.href) {
    const { href, ...anchorProps } = props;
    return (
      <a className={buttonClassName} href={href} {...anchorProps}>
        {children}
      </a>
    );
  }

  const buttonProps = props as ButtonAsButtonProps;
  const { type = 'button', ...restButtonProps } = buttonProps;

  return (
    <button className={buttonClassName} type={type} {...restButtonProps}>
      {children}
    </button>
  );
}
