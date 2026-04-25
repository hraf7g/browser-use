type AgentCursorProps = {
  x: number;
  y: number;
  clicking?: boolean;
};

export default function AgentCursor({ x, y, clicking = false }: AgentCursorProps) {
  return (
    <div
      aria-hidden="true"
      className={`agent-cursor${clicking ? ' is-clicking' : ''}`}
      style={{ transform: `translate(${x}px, ${y}px)` }}
    >
      <span className="agent-cursor__trail" />
      <svg viewBox="0 0 34 38" fill="none" xmlns="http://www.w3.org/2000/svg" className="agent-cursor__svg">
        <path
          d="M4 3L23.5 20L15.8 21.8L19.6 32.4L14 34L10.2 23.5L4.6 29.6L4 3Z"
          className="agent-cursor__arrow"
        />
      </svg>
      <span className="agent-cursor__dot" />
    </div>
  );
}
