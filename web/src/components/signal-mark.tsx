interface SignalMarkProps {
  compact?: boolean;
}

export function SignalMark({ compact = false }: SignalMarkProps) {
  return (
    <span className="signal-mark" aria-hidden="true">
      {[0, 1, 2, 3, 4].map((bar) => (
        <span key={bar} style={{ height: compact ? 5 + bar * 2 : 7 + bar * 3 }} />
      ))}
    </span>
  );
}
