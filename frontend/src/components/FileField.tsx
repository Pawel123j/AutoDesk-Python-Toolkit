import { UploadCloud } from "lucide-react";

interface FileFieldProps {
  id: string;
  file: File | null;
  onChange: (file: File | null) => void;
  helper: string;
}

export function FileField({ id, file, onChange, helper }: FileFieldProps) {
  return (
    <label
      htmlFor={id}
      className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-zinc-700 bg-zinc-950/60 px-5 py-6 text-center transition hover:border-teal-400 hover:bg-teal-400/[0.04]"
    >
      <UploadCloud className="mb-3 h-8 w-8 text-teal-300" aria-hidden="true" />
      <span className="text-sm font-semibold text-zinc-100">{file ? file.name : "Choose CSV file"}</span>
      <span className="mt-2 max-w-md text-xs leading-5 text-zinc-400">{helper}</span>
      <input
        id={id}
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
    </label>
  );
}
