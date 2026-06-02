import type { ReactNode } from "react";

interface DataTableProps<T> {
  title: string;
  rows: T[];
  columns: Array<{
    key: string;
    header: string;
    render: (row: T) => ReactNode;
  }>;
}

export function DataTable<T>({ title, rows, columns }: DataTableProps<T>) {
  return (
    <section className="rounded-3xl border border-white/10 bg-graphite/80 p-5 shadow-glass">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-white">{title}</h2>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-slate-300">{rows.length} rows</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.25em] text-slate-500">
            <tr>
              {columns.map((column) => (
                <th className="border-b border-white/10 pb-3 font-medium" key={column.key}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10 text-slate-200">
            {rows.map((row, index) => (
              <tr className="transition hover:bg-white/[0.03]" key={index}>
                {columns.map((column) => (
                  <td className="py-3 pr-4" key={column.key}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
