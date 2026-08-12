'use client';

import type { ReactNode } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  ClipboardList,
  HeartHandshake,
  Languages,
  ShieldCheck,
  Stethoscope,
} from 'lucide-react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void | Promise<void>;
  errorMessage?: string | null;
  ended?: boolean;
  isStarting?: boolean;
}

export function WelcomeView({
  startButtonText,
  onStartCall,
  errorMessage,
  ended = false,
  isStarting = false,
}: WelcomeViewProps) {
  const title = ended ? 'Your consultation has ended.' : 'Health support,';
  const highlightedTitle = ended
    ? 'We are here whenever you need us.'
    : 'just a conversation away.';

  return (
    <main className="min-h-svh overflow-hidden bg-[#f2fbf6] text-[#17382b]">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Image
          src="/image.png"
          alt="ASHA Sathi"
          width={153}
          height={50}
          priority
          className="h-auto w-[142px] sm:w-[153px]"
        />
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-full border border-[#d6ecdf] bg-white/80 px-3 py-1.5 text-[10px] font-bold tracking-[0.08em] text-[#187451] uppercase shadow-sm transition hover:bg-white sm:px-4 sm:text-[11px]"
          >
            <ClipboardList size={14} aria-hidden="true" />
            Human-help requests
          </Link>
          <p className="hidden font-mono text-[10px] font-bold tracking-[0.12em] text-[#1d392e] uppercase sm:block">
            Voice health support
          </p>
          <p className="font-mono text-[9px] font-bold tracking-[0.1em] text-[#1d392e] uppercase sm:text-[10px]">
            Murf Falcon
          </p>
        </div>
      </header>

      <section className="relative mx-auto grid w-full max-w-7xl items-center gap-10 px-5 pt-6 pb-12 sm:px-8 lg:grid-cols-[1.06fr_0.94fr] lg:px-10 lg:pt-14 lg:pb-20">
        <div className="pointer-events-none absolute top-1/2 -left-36 size-80 -translate-y-1/2 rounded-full bg-[#d9f4e5] blur-3xl" />

        <div className="relative">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#d6ecdf] bg-white/80 px-4 py-2 text-xs font-semibold text-[#187451] shadow-sm">
            <Activity size={16} aria-hidden="true" />
            Built for ASHA workers &amp; frontline health teams
          </div>

          <h1 className="max-w-xl text-4xl font-extrabold tracking-[-0.055em] text-[#163629] sm:text-5xl lg:text-6xl lg:leading-[1.07]">
            {title} <span className="text-[#168457]">{highlightedTitle}</span>
          </h1>

          <p className="mt-6 max-w-xl text-base leading-7 text-[#62786d] sm:text-lg sm:leading-8">
            ASHA Sathi is a multilingual voice assistant for basic symptom screening, maternal and
            child-health awareness, preventive guidance, and referral support.
          </p>

          <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-2">
            <Feature
              icon={<Stethoscope size={21} />}
              title="Symptom screening"
              text="Ask relevant follow-up questions."
            />
            <Feature
              icon={<HeartHandshake size={21} />}
              title="Maternal & child health"
              text="Support preventive health awareness."
            />
            <Feature
              icon={<ShieldCheck size={21} />}
              title="Referral guidance"
              text="Recognise warning signs early."
            />
            <Feature
              icon={<Languages size={21} />}
              title="Multilingual"
              text="Hindi, English & Hinglish."
            />
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-xl rounded-[30px] border border-[#dceee4] bg-white/95 p-5 shadow-[0_24px_70px_rgba(19,94,63,0.13)] backdrop-blur sm:p-7">
          <div className="flex items-center gap-3">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-[#e8f8ef] text-[#158052]">
              <HeartHandshake size={25} aria-hidden="true" />
            </div>
            <div>
              <h2 className="font-bold text-[#19392c]">
                {ended ? 'Start another consultation' : 'Start a health consultation'}
              </h2>
              <p className="mt-0.5 text-sm text-[#71877d]">Voice-first · Simple · Multilingual</p>
            </div>
          </div>

          {errorMessage ? (
            <div
              role="alert"
              className="mt-6 rounded-2xl border border-[#f4c8bf] bg-[#fff6f3] p-4 text-sm leading-6 text-[#8f3225]"
            >
              <p className="font-bold">Microphone access is needed</p>
              <p className="mt-1">{errorMessage}</p>
            </div>
          ) : (
            <div className="mt-6 rounded-2xl bg-[#effaf4] p-5 text-sm leading-6 text-[#557166]">
              <p className="font-bold text-[#2c5845]">
                Namaste! <span aria-hidden="true">🙏</span>
              </p>
              <p className="mt-2">
                बोलकर अपने patient की health concern बताइए। मैं एक समय में एक सवाल पूछकर आपकी सहायता
                करूँगी।
              </p>
            </div>
          )}

          <button
            type="button"
            onClick={onStartCall}
            disabled={isStarting}
            className="mt-6 flex min-h-16 w-full items-center justify-center gap-3 rounded-full bg-[#0f7a4f] px-6 text-base font-bold text-white shadow-[0_10px_18px_rgba(15,122,79,0.23)] transition hover:bg-[#09613e] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#0f7a4f] disabled:cursor-wait disabled:opacity-75"
          >
            {isStarting ? 'Connecting…' : startButtonText}
            {!isStarting && <ArrowRight size={20} aria-hidden="true" />}
          </button>

          <p className="mt-5 flex items-center justify-center gap-2 text-center text-xs leading-5 text-[#7a9086]">
            <ShieldCheck size={15} aria-hidden="true" />
            General health support · Not a replacement for a doctor
          </p>
        </div>
      </section>
    </main>
  );
}

function Feature({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-2xl border border-[#dfefe6] bg-white/75 p-4 shadow-sm">
      <div className="mb-3 flex size-9 items-center justify-center rounded-xl bg-[#eaf8f0] text-[#168457]">
        {icon}
      </div>
      <h2 className="font-bold text-[#294438]">{title}</h2>
      <p className="mt-1 text-sm leading-5 text-[#758b80]">{text}</p>
    </div>
  );
}
