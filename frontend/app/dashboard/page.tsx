import Image from 'next/image';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { CallAnalyticsSection } from '@/components/app/call-analytics-section';
import { EscalationsDashboard } from '@/components/app/escalations-dashboard';

export default function DashboardPage() {
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

      <div className="mx-auto w-full max-w-7xl px-5 pb-12 sm:px-8 lg:px-10">
        <CallAnalyticsSection />
        <EscalationsDashboard embedded />
      </div>
    </main>
  );
}
