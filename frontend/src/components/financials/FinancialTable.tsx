'use client';

/**
 * Reusable financial table component.
 *
 * Displays financial statement data horizontally (periods as columns).
 * Each row has: label | raw value per period | optional cs_* pct column.
 * Toggle switch shows/hides common-size percentage columns.
 *
 * Features:
 * - Sticky first column (row label)
 * - Horizontal scrolling for many periods
 * - Collapsible row sections (e.g. "Operating Expenses")
 * - Red/green colouring for positive/negative values
 * - Toggle between $ millions and % view
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatFinancialValue, formatCommonSize, signColorClass } from '@/utils/formatters';

export interface FinancialRow {
  /** Unique key */
  key: string;
  /** Display label (indentation supported via level) */
  label: string;
  /** Indentation depth (0 = top-level, 1 = sub-item) */
  level?: number;
  /** Whether this row is a section header (bold, collapsible) */
  isHeader?: boolean;
  /** The child keys controlled by this header */
  childKeys?: string[];
  /** Values per period column index */
  values: (number | null)[];
  /** Common-size percentage values (same order as values) */
  csValues?: (number | null)[];
  /** Override sign logic: true means "positive is good", false means "negative is good" */
  positiveIsGood?: boolean;
}

interface FinancialTableProps {
  /** Column header labels (e.g. "FY2023", "FY2022", …) */
  periods: string[];
  rows: FinancialRow[];
  currency?: string;
  title?: string;
  /** Whether to show the $ / % toggle */
  showToggle?: boolean;
}

export function FinancialTable({
  periods,
  rows,
  currency = 'USD',
  title,
  showToggle = true,
}: FinancialTableProps) {
  const [showCommonSize, setShowCommonSize] = useState(false);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  function toggleCollapse(key: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  // Build set of hidden keys (children of collapsed headers)
  const hiddenKeys = new Set<string>();
  for (const row of rows) {
    if (row.isHeader && row.childKeys && collapsed.has(row.key)) {
      row.childKeys.forEach((k) => hiddenKeys.add(k));
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        {title && <h3 className="text-sm font-semibold text-foreground">{title}</h3>}
        {showToggle && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={!showCommonSize ? 'text-foreground font-medium' : ''}>
              $ Millions
            </span>
            <button
              role="switch"
              aria-checked={showCommonSize}
              onClick={() => setShowCommonSize((v) => !v)}
              className={cn(
                'relative inline-flex h-5 w-9 rounded-full transition-colors border border-border',
                showCommonSize ? 'bg-primary' : 'bg-muted',
              )}
            >
              <span
                className={cn(
                  'inline-block h-4 w-4 rounded-full bg-white shadow transition-transform mt-0.5',
                  showCommonSize ? 'translate-x-4 ml-0.5' : 'translate-x-0.5',
                )}
              />
            </button>
            <span className={showCommonSize ? 'text-foreground font-medium' : ''}>
              % Structure
            </span>
          </div>
        )}
      </div>

      {/* Scrollable table */}
      <div className="overflow-x-auto scroll-thin">
        <table className="financial-table min-w-max w-full">
          <thead>
            <tr>
              {/* Sticky label column */}
              <th className="text-left min-w-52 sticky left-0 bg-card z-10">
                {title ?? 'Item'}
              </th>
              {periods.map((p) => (
                <th key={p} className="min-w-28">
                  {p}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              if (hiddenKeys.has(row.key)) return null;

              return (
                <tr
                  key={row.key}
                  className={cn(row.isHeader && 'font-semibold')}
                >
                  {/* Sticky label */}
                  <td
                    className={cn(
                      'text-left sticky left-0 bg-card z-10 border-b border-border/50',
                      'py-1.5 px-3',
                    )}
                    style={{ paddingLeft: `${(row.level ?? 0) * 16 + 12}px` }}
                  >
                    <div className="flex items-center gap-1">
                      {row.isHeader && row.childKeys && (
                        <button
                          onClick={() => toggleCollapse(row.key)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          {collapsed.has(row.key) ? (
                            <ChevronRight className="h-3 w-3" />
                          ) : (
                            <ChevronDown className="h-3 w-3" />
                          )}
                        </button>
                      )}
                      <span
                        className={cn(
                          row.isHeader ? 'text-foreground' : 'text-muted-foreground',
                          row.level === 0 && !row.isHeader && 'text-foreground',
                        )}
                      >
                        {row.label}
                      </span>
                    </div>
                  </td>

                  {/* Value cells */}
                  {periods.map((_, i) => {
                    const rawVal = row.values[i] ?? null;
                    const csVal = row.csValues?.[i] ?? null;
                    const displayVal = showCommonSize ? csVal : rawVal;

                    return (
                      <td
                        key={i}
                        className={cn(
                          'text-right py-1.5 px-3 border-b border-border/50 font-mono tabular-nums',
                          !row.isHeader && displayVal != null && signColorClass(
                            (row.positiveIsGood ?? true) ? displayVal : -displayVal,
                          ),
                        )}
                      >
                        {displayVal == null
                          ? '—'
                          : showCommonSize
                          ? formatCommonSize(displayVal)
                          : formatFinancialValue(displayVal, currency)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
