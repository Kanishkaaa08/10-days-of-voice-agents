'use client';

import { useCallback, useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { AlertCircle, ArrowLeft, RefreshCw, ShieldCheck } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Escalation {
  id: number;
  reference_id: string;
  caller_identifier: string | null;
  caller_name: string | null;
  reason: string;
  summary: string;
  agent_checks: string | null;
  urgency: string;
  language: string | null;
  preferred_followup: string | null;
  status: string;
  created_at: string;
}

const STATUS_OPTIONS = ['Open', 'In Progress', 'Resolved'] as const;

function formatReason(reason: string) {
  return reason.replace(/_/g, ' ');
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

function urgencyClasses(urgency: string) {
  switch (urgency.toLowerCase()) {
    case 'high':
      return 'bg-[#fde8e4] text-[#9b2c1f] border-[#f4c8bf]';
    case 'low':
      return 'bg-[#eef5f1] text-[#4a6658] border-[#d6ecdf]';
    default:
      return 'bg-[#fff6e8] text-[#8a5a12] border-[#f0ddb8]';
  }
}

function statusClasses(status: string) {
  switch (status) {
    case 'In Progress':
      return 'bg-[#e8f0ff] text-[#1f4f9c] border-[#c8d9f7]';
    case 'Resolved':
      return 'bg-[#e8f8ef] text-[#168457] border-[#c8ead6]';
    default:
      return 'bg-[#fff6e8] text-[#8a5a12] border-[#f0ddb8]';
  }
}

export function EscalationsDashboard() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const loadEscalations = useCallback(async () => {
    setError(null);

    try {
      const response = await fetch('/api/escalations', { cache: 'no-store' });

      if (!response.ok) {
        throw new Error('Unable to load human-help requests');
      }

      const data = (await response.json()) as Escalation[];
      setEscalations(data);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : 'Unable to load human-help requests'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadEscalations();
    const interval = window.setInterval(() => {
      void loadEscalations();
    }, 10000);

    return () => window.clearInterval(interval);
  }, [loadEscalations]);

  const handleStatusChange = async (id: number, status: string) => {
    setUpdatingId(id);

    try {
      const response = await fetch(`/api/escalations/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error('Unable to update status');
      }

      const updated = (await response.json()) as Escalation;
      setEscalations((current) =>
        current.map((item) => (item.id === updated.id ? updated : item))
      );
    } catch {
      setError('Unable to update request status. Please try again.');
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <main className="min-h-svh bg-[#f2fbf6] text-[#17382b]">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Image
          src="/image.png"
          alt="ASHA Sathi"
          width={153}
          height={50}
          priority
          className="h-auto w-[142px] sm:w-[153px]"
        />
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-full border border-[#d6ecdf] bg-white px-4 py-2 text-sm font-semibold text-[#187451] shadow-sm transition hover:bg-[#f7fcf9]"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Back to voice agent
        </Link>
      </header>

      <section className="mx-auto w-full max-w-7xl px-5 pb-12 sm:px-8 lg:px-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-bold tracking-[0.14em] text-[#197451] uppercase">
              Day 7 · Human help
            </p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[#19392c] sm:text-4xl">
              Human-help requests
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-[#62786d]">
              Review escalation requests created when ASHA Sathi identifies a red-flag symptom or
              a diagnosis request and the caller gives permission to share a short summary.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setLoading(true);
              void loadEscalations();
            }}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-[#d6ecdf] bg-white px-4 py-2 text-sm font-semibold text-[#187451] shadow-sm transition hover:bg-[#f7fcf9]"
          >
            <RefreshCw size={16} aria-hidden="true" />
            Refresh
          </button>
        </div>

        {error ? (
          <div
            role="alert"
            className="mt-8 flex items-start gap-3 rounded-2xl border border-[#f4c8bf] bg-[#fff6f3] p-4 text-sm leading-6 text-[#8f3225]"
          >
            <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-bold">Could not load requests</p>
              <p className="mt-1">{error}</p>
              <p className="mt-2 text-[#a24b3f]">
                Make sure the backend API server is running on port 5001.
              </p>
            </div>
          </div>
        ) : null}

        {loading ? (
          <div className="mt-10 rounded-[30px] border border-[#dceee4] bg-white p-10 text-center shadow-[0_24px_70px_rgba(19,94,63,0.08)]">
            <p className="text-sm font-semibold text-[#557166]">Loading human-help requests…</p>
          </div>
        ) : escalations.length === 0 ? (
          <div className="mt-10 rounded-[30px] border border-[#dceee4] bg-white p-10 text-center shadow-[0_24px_70px_rgba(19,94,63,0.08)]">
            <p className="text-lg font-bold text-[#294438]">No human-help requests yet</p>
            <p className="mt-2 text-sm leading-6 text-[#758b80]">
              Requests appear here after ASHA Sathi creates an escalation with caller consent.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid gap-5">
            {escalations.map((item) => (
              <article
                key={item.id}
                className="rounded-[28px] border border-[#dceee4] bg-white p-5 shadow-[0_18px_50px_rgba(19,94,63,0.08)] sm:p-6"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-mono text-lg font-bold text-[#19392c]">
                        {item.reference_id}
                      </h2>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${urgencyClasses(item.urgency)}`}
                      >
                        {item.urgency} urgency
                      </span>
                      <span
                        className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClasses(item.status)}`}
                      >
                        {item.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-[#71877d]">{formatDate(item.created_at)}</p>
                  </div>

                  <div className="min-w-[180px]">
                    <label className="mb-2 block text-xs font-semibold tracking-[0.08em] text-[#557166] uppercase">
                      Update status
                    </label>
                    <Select
                      value={item.status}
                      onValueChange={(value) => void handleStatusChange(item.id, value)}
                      disabled={updatingId === item.id}
                    >
                      <SelectTrigger className="w-full border-[#d6ecdf] bg-[#f7fcf9]">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        {STATUS_OPTIONS.map((status) => (
                          <SelectItem key={status} value={status}>
                            {status}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <dl className="mt-5 grid gap-4 sm:grid-cols-2">
                  <Detail label="Reason" value={formatReason(item.reason)} />
                  <Detail label="Language" value={item.language || 'Not specified'} />
                  <Detail label="Caller name" value={item.caller_name || 'Not provided'} />
                  <Detail
                    label="Preferred follow-up"
                    value={item.preferred_followup || 'Not specified'}
                  />
                </dl>

                <div className="mt-5 grid gap-4">
                  <TextBlock label="Short summary" value={item.summary} />
                  <TextBlock
                    label="What agent checked"
                    value={item.agent_checks || 'Not recorded'}
                  />
                </div>
              </article>
            ))}
          </div>
        )}

        <p className="mt-8 flex items-center justify-center gap-2 text-xs text-[#7c9288]">
          <ShieldCheck size={15} aria-hidden="true" />
          Only short sanitized summaries are stored — no full transcripts
        </p>
      </section>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#dfefe6] bg-[#f7fcf9] p-4">
      <dt className="text-xs font-semibold tracking-[0.08em] text-[#557166] uppercase">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-[#294438]">{value}</dd>
    </div>
  );
}

function TextBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#dfefe6] bg-[#f7fcf9] p-4">
      <p className="text-xs font-semibold tracking-[0.08em] text-[#557166] uppercase">{label}</p>
      <p className="mt-2 text-sm leading-6 text-[#294438]">{value}</p>
    </div>
  );
}
