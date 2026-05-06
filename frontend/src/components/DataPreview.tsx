interface DataPreviewProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
}

export function DataPreview({ columns, rows }: DataPreviewProps) {
  if (!rows.length) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-5 text-sm text-zinc-400">
        The cleaned file has no previewable rows.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950/70">
      <div className="max-h-[420px] overflow-auto">
        <table className="min-w-full divide-y divide-zinc-800 text-sm">
          <thead className="sticky top-0 bg-zinc-950">
            <tr>
              {columns.map((column) => (
                <th key={column} className="whitespace-nowrap px-4 py-3 text-left font-semibold text-zinc-200">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-white/[0.03]">
                {columns.map((column) => (
                  <td key={column} className="max-w-[220px] truncate px-4 py-3 text-zinc-300">
                    {formatCell(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "null";
  }
  return String(value);
}
