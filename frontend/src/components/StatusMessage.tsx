import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

interface StatusMessageProps {
  tone: "success" | "error";
  children: ReactNode;
}

export function StatusMessage({ tone, children }: StatusMessageProps) {
  const Icon = tone === "success" ? CheckCircle2 : AlertTriangle;
  const styles =
    tone === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
      : "border-rose-500/30 bg-rose-500/10 text-rose-100";

  return (
    <div className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${styles}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
