'use client';

import { useCallback, useEffect, useState } from 'react';
import { AlertCircle, BarChart3, RefreshCw } from 'lucide-react';

interface AnalyticsSummary {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
}

export function CallAnalyticsSection() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    setError(null);

    try {
      const response = await fetch('/api/analytics', { cache: 'no-store' });

      if (!response.ok) {
        throw new Error('Unable to load call analytics');
      }

      const data = (await response.json()) as AnalyticsSummary;
      setAnalytics(data);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error ? fetchError.message : 'Unable to load call analytics'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalytics();
    const interval = window.setInterval(() => {
      void loadAnalytics();
    }, 10000);

    return () => window.clearInterval(interval);
  }, [loadAnalytics]);

  return (
    <section className="mb-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold tracking-[0.14em] text-[#197451] uppercase">
            Day 8 · Call analytics
          </p>
          <h2 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[#19392c] sm:text-3xl">
            ASHA Saathi analytics
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#62786d]">
            Live counts from real browser voice calls. A successful call means the caller received
            safe guidance or an appropriate human-help escalation was created.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setLoading(true);
            void loadAnalytics();
          }}
          className="inline-flex items-center justify-center gap-2 rounded-full border border-[#d6ecdf] bg-white px-4 py-2 text-sm font-semibold text-[#187451] shadow-sm transition hover:bg-[#f7fcf9]"
        >
          <RefreshCw size={16} aria-hidden="true" />
          Refresh analytics
        </button>
      </div>

      {error ? (
        <div
          role="alert"
          className="mt-6 flex items-start gap-3 rounded-2xl border border-[#f4c8bf] bg-[#fff6f3] p-4 text-sm leading-6 text-[#8f3225]"
        >
          <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-bold">Could not load analytics</p>
            <p className="mt-1">{error}</p>
            <p className="mt-2 text-[#a24b3f]">
              Make sure the backend API server is running on port 5001.
            </p>
          </div>
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Total calls"
          value={loading ? null : analytics?.total_calls ?? 0}
          loading={loading}
          accent="bg-[#e8f8ef] text-[#168457]"
        />
        <MetricCard
          label="Successful calls"
          value={loading ? null : analytics?.successful_calls ?? 0}
          loading={loading}
          accent="bg-[#e8f8ef] text-[#168457]"
        />
        <MetricCard
          label="Failed calls"
          value={loading ? null : analytics?.failed_calls ?? 0}
          loading={loading}
          accent="bg-[#fde8e4] text-[#9b2c1f]"
        />
      </div>

      <p className="mt-4 flex items-center gap-2 text-xs text-[#7c9288]">
        <BarChart3 size={15} aria-hidden="true" />
        Counts refresh automatically every 10 seconds. No transcripts or medical details are stored.
      </p>
    </section>
  );
}

function MetricCard({
  label,
  value,
  loading,
  accent,
}: {
  label: string;
  value: number | null;
  loading: boolean;
  accent: string;
}) {
  return (
    <article
      className="rounded-[28px] border border-[#dceee4] bg-white p-6 shadow-[0_18px_50px_rgba(19,94,63,0.08)]"
    >
      <p className="text-xs font-bold tracking-[0.14em] text-[#557166] uppercase">{label}</p>
      <div className="mt-4 flex items-center gap-3">
        <div className={`flex size-11 items-center justify-center rounded-2xl ${accent}`}>
          <BarChart3 size={20} aria-hidden="true" />
        </div>
        <p className="text-4xl font-extrabold tracking-[-0.04em] text-[#19392c]">
          {loading ? '…' : value}
        </p>
      </div>
    </article>
  );
}
