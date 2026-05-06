export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface CleanCsvResponse {
  file_name: string;
  original_rows: number;
  cleaned_rows: number;
  empty_rows_removed: number;
  duplicate_rows_removed: number;
  columns: string[];
  preview: Array<Record<string, unknown>>;
}

export interface FileSorterResponse {
  categories: Record<string, string[]>;
  total_files: number;
}

export interface HistoryItem {
  id: number;
  created_at: string;
  action_type: string;
  file_name: string;
  details: Record<string, unknown>;
}

export interface HistoryResponse {
  items: HistoryItem[];
}

export async function cleanCsv(file: File): Promise<CleanCsvResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/csv/clean`, {
    method: "POST",
    body: formData,
  });
  await ensureOk(response);
  return response.json();
}

export async function uploadAndDownload(endpoint: string, file: File, fallbackName: string): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
  });
  await ensureOk(response);

  const blob = await response.blob();
  const fileName = filenameFromDisposition(response.headers.get("content-disposition")) ?? fallbackName;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  return fileName;
}

export async function simulateFileSorter(fileNames: string[]): Promise<FileSorterResponse> {
  const response = await fetch(`${API_BASE_URL}/api/file-sorter/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_names: fileNames }),
  });
  await ensureOk(response);
  return response.json();
}

export async function getHistory(): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/history`);
  await ensureOk(response);
  return response.json();
}

export async function deleteHistory(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/history`, { method: "DELETE" });
  await ensureOk(response);
}

async function ensureOk(response: Response): Promise<void> {
  if (response.ok) {
    return;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    if (typeof payload?.detail === "string") {
      throw new Error(payload.detail);
    }
    if (payload?.detail) {
      throw new Error(JSON.stringify(payload.detail));
    }
  }

  throw new Error(`Request failed with status ${response.status}`);
}

function filenameFromDisposition(disposition: string | null): string | null {
  if (!disposition) {
    return null;
  }
  const encodedMatch = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (encodedMatch?.[1]) {
    return decodeURIComponent(encodedMatch[1]);
  }
  const match = /filename="?([^"]+)"?/i.exec(disposition);
  return match?.[1] ?? null;
}
