import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Clock3,
  Database,
  Download,
  ExternalLink,
  FileSpreadsheet,
  FileText,
  FolderTree,
  Home,
  Loader2,
  RefreshCcw,
  Sparkles,
  Table2,
  Trash2,
  Wand2,
  type LucideIcon,
} from "lucide-react";
import { DataPreview } from "./components/DataPreview";
import { FileField } from "./components/FileField";
import { StatusMessage } from "./components/StatusMessage";
import {
  API_BASE_URL,
  CleanCsvResponse,
  FileSorterResponse,
  HistoryItem,
  cleanCsv,
  deleteHistory,
  getHistory,
  simulateFileSorter,
  uploadAndDownload,
} from "./lib/api";

type ViewKey = "home" | "cleaner" | "converter" | "reports" | "sorter" | "history";

const navigation = [
  { key: "home", label: "Home", icon: Home },
  { key: "cleaner", label: "CSV Cleaner", icon: Wand2 },
  { key: "converter", label: "CSV to Excel", icon: FileSpreadsheet },
  { key: "reports", label: "Reports", icon: FileText },
  { key: "sorter", label: "File Sorter", icon: FolderTree },
  { key: "history", label: "History", icon: Clock3 },
] satisfies Array<{ key: ViewKey; label: string; icon: LucideIcon }>;

const featureCards = [
  {
    key: "cleaner",
    title: "Clean CSV data",
    description: "Remove blank rows, deduplicate records, normalize headers, and inspect a preview table.",
    icon: Wand2,
    accent: "text-teal-300 bg-teal-400/10 border-teal-400/20",
  },
  {
    key: "converter",
    title: "Export Excel files",
    description: "Turn CSV uploads into downloadable XLSX workbooks using Pandas and OpenPyXL.",
    icon: FileSpreadsheet,
    accent: "text-emerald-300 bg-emerald-400/10 border-emerald-400/20",
  },
  {
    key: "reports",
    title: "Generate reports",
    description: "Create text or HTML reports with row counts, columns, missing values, and averages.",
    icon: FileText,
    accent: "text-amber-300 bg-amber-400/10 border-amber-400/20",
  },
  {
    key: "sorter",
    title: "Sort file names",
    description: "Simulate folder categorization for images, documents, spreadsheets, archives, and other files.",
    icon: FolderTree,
    accent: "text-pink-300 bg-pink-400/10 border-pink-400/20",
  },
] satisfies Array<{
  key: ViewKey;
  title: string;
  description: string;
  icon: LucideIcon;
  accent: string;
}>;

function App() {
  const [activeView, setActiveView] = useState<ViewKey>("home");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    try {
      const response = await getHistory();
      setHistory(response.items);
      setHistoryError(null);
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : "Could not load history.");
    }
  }, []);

  useEffect(() => {
    void refreshHistory();
  }, [refreshHistory]);

  const content = useMemo(() => {
    switch (activeView) {
      case "cleaner":
        return <CleanerView onComplete={refreshHistory} />;
      case "converter":
        return <ConverterView onComplete={refreshHistory} />;
      case "reports":
        return <ReportsView onComplete={refreshHistory} />;
      case "sorter":
        return <SorterView onComplete={refreshHistory} />;
      case "history":
        return <HistoryView history={history} error={historyError} onRefresh={refreshHistory} />;
      default:
        return <HomeView history={history} onNavigate={setActiveView} />;
    }
  }, [activeView, history, historyError, refreshHistory]);

  return (
    <div className="min-h-screen text-zinc-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:flex-row lg:px-8">
        <aside className="lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)] lg:w-72">
          <div className="flex h-full flex-col justify-between rounded-lg border border-zinc-800 bg-zinc-950/80 p-4 shadow-panel backdrop-blur">
            <div>
              <div className="mb-6 flex items-center gap-3 px-2">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-teal-400/20 bg-teal-400/10">
                  <Sparkles className="h-5 w-5 text-teal-200" aria-hidden="true" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">AutoDesk</p>
                  <p className="text-xs text-zinc-400">Python Toolkit</p>
                </div>
              </div>
              <nav className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1" aria-label="Primary navigation">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeView === item.key;
                  return (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => setActiveView(item.key)}
                      className={`flex items-center gap-3 rounded-lg px-3 py-3 text-left text-sm font-medium transition ${
                        isActive
                          ? "bg-white text-zinc-950"
                          : "text-zinc-300 hover:bg-white/[0.06] hover:text-white"
                      }`}
                    >
                      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
            <div className="mt-6 rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
                <Database className="h-4 w-4 text-emerald-300" aria-hidden="true" />
                Local first
              </div>
              <p className="mt-2 text-xs leading-5 text-zinc-400">
                FastAPI, Pandas, SQLite, React, TypeScript, Tailwind, and no paid APIs.
              </p>
            </div>
          </div>
        </aside>
        <main className="min-w-0 flex-1">{content}</main>
      </div>
    </div>
  );
}

function HomeView({ history, onNavigate }: { history: HistoryItem[]; onNavigate: (view: ViewKey) => void }) {
  const latestAction = history[0];

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-zinc-800 bg-zinc-950/75 p-6 shadow-panel sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <p className="mb-3 text-sm font-semibold text-teal-200">Python automation dashboard</p>
            <h1 className="text-3xl font-bold leading-tight text-white sm:text-5xl">AutoDesk Python Toolkit</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-300">
              A polished local web app for cleaning CSV files, converting them to Excel, generating simple reports,
              simulating file sorting, and tracking every action in SQLite.
            </p>
          </div>
          <a
            href={`${API_BASE_URL}/docs`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex w-fit items-center gap-2 rounded-md border border-teal-400/40 bg-teal-400/10 px-4 py-2.5 text-sm font-semibold text-teal-100 transition hover:bg-teal-400/20"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            API Docs
          </a>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          <Metric label="History events" value={history.length.toString()} tone="teal" />
          <Metric label="Backend" value="FastAPI" tone="amber" />
          <Metric label="Storage" value="SQLite" tone="pink" />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {featureCards.map((feature) => {
          const Icon = feature.icon;
          return (
            <button
              key={feature.key}
              type="button"
              onClick={() => onNavigate(feature.key)}
              className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-5 text-left shadow-panel transition hover:-translate-y-0.5 hover:border-zinc-600 hover:bg-zinc-900/80"
            >
              <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg border ${feature.accent}`}>
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-semibold text-white">{feature.title}</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">{feature.description}</p>
            </button>
          );
        })}
      </section>

      <section className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-5">
        <div className="flex items-center gap-3">
          <Clock3 className="h-5 w-5 text-zinc-300" aria-hidden="true" />
          <h2 className="text-lg font-semibold text-white">Latest activity</h2>
        </div>
        {latestAction ? (
          <p className="mt-3 text-sm leading-6 text-zinc-300">
            {latestAction.action_type} processed <span className="font-semibold text-white">{latestAction.file_name}</span>{" "}
            on {formatDate(latestAction.created_at)}.
          </p>
        ) : (
          <p className="mt-3 text-sm leading-6 text-zinc-400">
            No actions yet. Upload the sample CSV from the examples folder to see the workflow in motion.
          </p>
        )}
      </section>
    </div>
  );
}

function CleanerView({ onComplete }: { onComplete: () => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CleanCsvResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await cleanCsv(file);
      setResult(response);
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV cleaning failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ToolShell
      icon={Wand2}
      title="CSV Cleaner"
      description="Remove blank rows, drop duplicates, normalize column names, and preview the cleaned dataset."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FileField
          id="cleaner-file"
          file={file}
          onChange={setFile}
          helper="Maximum upload size is 10 MB. The API returns a cleaned preview without storing the full upload."
        />
        <PrimaryButton loading={loading} icon={Table2}>
          Clean CSV
        </PrimaryButton>
      </form>
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {result && (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-4">
            <Metric label="Original rows" value={result.original_rows.toString()} tone="teal" />
            <Metric label="Cleaned rows" value={result.cleaned_rows.toString()} tone="emerald" />
            <Metric label="Empty rows removed" value={result.empty_rows_removed.toString()} tone="amber" />
            <Metric label="Duplicates removed" value={result.duplicate_rows_removed.toString()} tone="pink" />
          </div>
          <DataPreview columns={result.columns} rows={result.preview} />
        </div>
      )}
    </ToolShell>
  );
}

function ConverterView({ onComplete }: { onComplete: () => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadName, setDownloadName] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setLoading(true);
    setError(null);
    setDownloadName(null);
    try {
      const name = await uploadAndDownload("/api/csv/to-excel", file, "converted.xlsx");
      setDownloadName(name);
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV conversion failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ToolShell
      icon={FileSpreadsheet}
      title="CSV to Excel Converter"
      description="Upload a CSV file and receive a downloadable XLSX workbook generated by the backend."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FileField
          id="converter-file"
          file={file}
          onChange={setFile}
          helper="The workbook keeps your CSV rows and columns intact and logs the conversion in SQLite."
        />
        <PrimaryButton loading={loading} icon={Download}>
          Convert and Download
        </PrimaryButton>
      </form>
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {downloadName && <StatusMessage tone="success">Downloaded {downloadName}</StatusMessage>}
    </ToolShell>
  );
}

function ReportsView({ onComplete }: { onComplete: () => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<"txt" | "html">("txt");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadName, setDownloadName] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setLoading(true);
    setError(null);
    setDownloadName(null);
    try {
      const fallback = format === "html" ? "report.html" : "report.txt";
      const name = await uploadAndDownload(`/api/reports/generate?format=${format}`, file, fallback);
      setDownloadName(name);
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Report generation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ToolShell
      icon={FileText}
      title="Report Generator"
      description="Generate a downloadable report with row count, column count, missing values, and numeric averages."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FileField
          id="report-file"
          file={file}
          onChange={setFile}
          helper="Choose text for a lightweight report or HTML for a styled browser-ready report."
        />
        <div className="inline-flex rounded-lg border border-zinc-800 bg-zinc-950 p-1">
          {(["txt", "html"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setFormat(option)}
              className={`rounded-md px-4 py-2 text-sm font-semibold transition ${
                format === option ? "bg-white text-zinc-950" : "text-zinc-300 hover:bg-white/[0.06]"
              }`}
            >
              {option.toUpperCase()}
            </button>
          ))}
        </div>
        <PrimaryButton loading={loading} icon={BarChart3}>
          Generate Report
        </PrimaryButton>
      </form>
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {downloadName && <StatusMessage tone="success">Downloaded {downloadName}</StatusMessage>}
    </ToolShell>
  );
}

function SorterView({ onComplete }: { onComplete: () => Promise<void> }) {
  const [input, setInput] = useState("invoice.pdf\nteam-photo.jpg\nsales-q1.xlsx\nbackup.zip\nnotes.md\nscript.py");
  const [result, setResult] = useState<FileSorterResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const names = input
      .split(/[\n,]+/)
      .map((name) => name.trim())
      .filter(Boolean);

    if (!names.length) {
      setError("Enter at least one file name.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await simulateFileSorter(names);
      setResult(response);
      await onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "File sorting failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ToolShell
      icon={FolderTree}
      title="File Sorter Simulation"
      description="Paste example file names and see how the toolkit would categorize them into folders."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          rows={8}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-950/70 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-teal-400"
          placeholder="photo.png, budget.xlsx, archive.zip"
        />
        <PrimaryButton loading={loading} icon={FolderTree}>
          Sort File Names
        </PrimaryButton>
      </form>
      {error && <StatusMessage tone="error">{error}</StatusMessage>}
      {result && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Object.entries(result.categories).map(([category, files]) => (
            <div key={category} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-4">
              <h3 className="text-sm font-semibold text-white">{category}</h3>
              <p className="mt-1 text-xs text-zinc-500">{files.length} file{files.length === 1 ? "" : "s"}</p>
              <ul className="mt-4 space-y-2 text-sm text-zinc-300">
                {files.length ? files.map((name) => <li key={name} className="truncate">{name}</li>) : <li className="text-zinc-600">Empty</li>}
              </ul>
            </div>
          ))}
        </div>
      )}
    </ToolShell>
  );
}

function HistoryView({
  history,
  error,
  onRefresh,
}: {
  history: HistoryItem[];
  error: string | null;
  onRefresh: () => Promise<void>;
}) {
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleRefresh() {
    setLoading(true);
    await onRefresh();
    setLocalError(null);
    setLoading(false);
  }

  async function handleClear() {
    setLoading(true);
    try {
      await deleteHistory();
      await onRefresh();
      setLocalError(null);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not clear history.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ToolShell
      icon={Clock3}
      title="Processing History"
      description="SQLite keeps a compact local log of actions, file names, timestamps, and processing metadata."
      actions={
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 rounded-md border border-zinc-700 px-3 py-2 text-sm font-semibold text-zinc-200 transition hover:bg-white/[0.06]"
          >
            <RefreshCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
            Refresh
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="inline-flex items-center gap-2 rounded-md border border-rose-500/30 px-3 py-2 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/10"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Clear
          </button>
        </div>
      }
    >
      {(error || localError) && <StatusMessage tone="error">{error || localError}</StatusMessage>}
      <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950/70">
        <div className="max-h-[560px] overflow-auto">
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead className="bg-zinc-950">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-zinc-200">Date</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-200">Action</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-200">File name</th>
                <th className="px-4 py-3 text-left font-semibold text-zinc-200">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900">
              {history.length ? (
                history.map((item) => (
                  <tr key={item.id} className="hover:bg-white/[0.03]">
                    <td className="whitespace-nowrap px-4 py-3 text-zinc-300">{formatDate(item.created_at)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-100">{item.action_type}</td>
                    <td className="max-w-[240px] truncate px-4 py-3 text-zinc-300">{item.file_name}</td>
                    <td className="px-4 py-3 text-zinc-400">{formatDetails(item.details)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-zinc-500">
                    No processing history yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </ToolShell>
  );
}

function ToolShell({
  icon: Icon,
  title,
  description,
  children,
  actions,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950/75 p-5 shadow-panel sm:p-7">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-teal-400/20 bg-teal-400/10">
            <Icon className="h-5 w-5 text-teal-200" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white sm:text-3xl">{title}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">{description}</p>
          </div>
        </div>
        {actions}
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  );
}

function PrimaryButton({
  loading,
  icon: Icon,
  children,
}: {
  loading: boolean;
  icon: LucideIcon;
  children: string;
}) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-white px-5 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Icon className="h-4 w-4" aria-hidden="true" />}
      {loading ? "Working..." : children}
    </button>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "teal" | "emerald" | "amber" | "pink" }) {
  const toneClasses = {
    teal: "border-teal-400/20 bg-teal-400/10 text-teal-100",
    emerald: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
    amber: "border-amber-400/20 bg-amber-400/10 text-amber-100",
    pink: "border-pink-400/20 bg-pink-400/10 text-pink-100",
  };

  return (
    <div className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <p className="text-xs font-semibold uppercase opacity-75">{label}</p>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDetails(details: Record<string, unknown>): string {
  const entries = Object.entries(details);
  if (!entries.length) {
    return "-";
  }
  return entries
    .slice(0, 4)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(", ");
}

export default App;
