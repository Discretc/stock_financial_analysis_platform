import Link from 'next/link';
import { ArrowRight, BarChart3, TrendingUp, Shield } from 'lucide-react';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center min-h-screen px-4 text-center">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />

        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground mb-8">
          <span className="h-2 w-2 rounded-full bg-up animate-pulse" />
          Institutional-grade financial analytics
        </div>

        <h1 className="max-w-4xl text-5xl font-bold tracking-tight text-foreground sm:text-7xl">
          Bloomberg-grade{' '}
          <span className="text-primary">financial intelligence</span>
          {' '}for everyone
        </h1>

        <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
          Real-time stock data, common-size financial statements, YoY growth analysis,
          and institutional analytics — all in one platform.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4">
          <Link
            href="/stocks"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Start Analysing
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-2 rounded-lg border border-border px-6 py-3 text-sm font-semibold text-foreground hover:bg-muted transition-colors"
          >
            Sign In
          </Link>
        </div>
      </section>

      {/* Feature highlights */}
      <section className="max-w-6xl mx-auto px-4 py-24">
        <h2 className="text-3xl font-bold text-center mb-16">
          Professional-grade analytics
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {[
            {
              icon: BarChart3,
              title: 'Common-Size Statements',
              desc: 'Every line item as a % of revenue, total assets, or OCF — just like Bloomberg Terminal.',
            },
            {
              icon: TrendingUp,
              title: 'Real-Time Streaming',
              desc: 'Live price updates via WebSocket. Watchlists refresh automatically every 15 seconds.',
            },
            {
              icon: Shield,
              title: 'Enterprise Security',
              desc: 'Argon2 hashing, JWT rotation, RBAC, rate limiting, and OWASP-compliant headers.',
            },
          ].map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="rounded-xl border border-border bg-card p-6 hover:border-primary/50 transition-colors"
            >
              <div className="mb-4 inline-flex rounded-lg bg-primary/10 p-3">
                <Icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">{title}</h3>
              <p className="text-sm text-muted-foreground">{desc}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
