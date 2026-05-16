import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = { title: 'Dashboard' };

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Your financial overview at a glance.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { title: 'Watchlists', href: '/watchlists', desc: 'Track your favourite stocks' },
          { title: 'Stocks', href: '/stocks', desc: 'Search and analyse any stock' },
          { title: 'Portfolios', href: '/portfolios', desc: 'Manage your holdings' },
        ].map(({ title, href, desc }) => (
          <Link
            key={href}
            href={href}
            className="rounded-xl border border-border bg-card p-6 hover:border-primary/50 transition-colors"
          >
            <h2 className="font-semibold text-foreground">{title}</h2>
            <p className="text-sm text-muted-foreground mt-1">{desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
