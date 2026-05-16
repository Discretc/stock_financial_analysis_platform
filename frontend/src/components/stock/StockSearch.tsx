'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, Loader2 } from 'lucide-react';
import { useStockSearch } from '@/hooks/useStockData';
import { cn } from '@/lib/utils';
import type { SearchResult } from '@/types/stock';

interface StockSearchProps {
  className?: string;
  placeholder?: string;
  onSelect?: (result: SearchResult) => void;
}

export function StockSearch({ className, placeholder = 'Search stocks…', onSelect }: StockSearchProps) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const { data: results, isFetching } = useStockSearch(query, query.length >= 1);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleSelect(result: SearchResult) {
    setQuery('');
    setOpen(false);
    if (onSelect) {
      onSelect(result);
    } else {
      router.push(`/stocks/${result.ticker}`);
    }
  }

  function handleClear() {
    setQuery('');
    inputRef.current?.focus();
  }

  return (
    <div ref={containerRef} className={cn('relative w-full max-w-sm', className)}>
      <div className="relative flex items-center">
        <Search className="absolute left-3 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(e.target.value.length >= 1);
          }}
          onFocus={() => query.length >= 1 && setOpen(true)}
          placeholder={placeholder}
          className={cn(
            'w-full rounded-lg border border-input bg-background py-2 pl-9 pr-9 text-sm',
            'placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring',
            'transition-colors',
          )}
        />
        <div className="absolute right-3 flex items-center gap-1">
          {isFetching && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
          {query && !isFetching && (
            <button onClick={handleClear} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Dropdown */}
      {open && (
        <div className="absolute top-full left-0 right-0 z-50 mt-1 rounded-lg border border-border bg-popover shadow-lg overflow-hidden">
          {!results || results.length === 0 ? (
            <div className="px-4 py-3 text-sm text-muted-foreground">
              {isFetching ? 'Searching…' : `No results for "${query}"`}
            </div>
          ) : (
            <ul className="max-h-72 overflow-y-auto scroll-thin">
              {results.map((r) => (
                <li key={r.ticker}>
                  <button
                    onMouseDown={() => handleSelect(r)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-accent transition-colors"
                  >
                    <span className="font-mono font-semibold text-primary text-sm w-16 shrink-0">
                      {r.ticker}
                    </span>
                    <span className="text-sm text-foreground truncate">{r.name}</span>
                    {r.exchange && (
                      <span className="ml-auto text-xs text-muted-foreground shrink-0">
                        {r.exchange}
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
