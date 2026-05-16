/**
 * Shared UI utility — merges Tailwind class names.
 * Used by shadcn/ui components.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
