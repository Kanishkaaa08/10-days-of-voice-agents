'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Track } from 'livekit-client';
import { Activity, HeartPulse, MessageCircleMore, Mic, ShieldCheck, Volume2 } from 'lucide-react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import { AgentControlBar } from '@/components/agents-ui/agent-control-bar';

const WAVE_BARS = Array.from({ length: 7 }, (_, index) => index);

export function SessionView() {
  const session = useSessionContext();
  const { state: agentState } = useAgent();
  const { messages } = useSessionMessages(session);
  const [micError, setMicError] = useState<string | null>(null);
  const status = getStatus(agentState);

  return (
    <main
      className="flex min-h-svh flex-col bg-[#f5fbf8] text-[#17382b]"
      data-agent-state={agentState}
    >
      <header className="flex shrink-0 items-center justify-between border-b border-[#dceee4] bg-white/95 px-5 py-4 backdrop-blur sm:px-8">
        <Image
          src="/image.png"
          alt="ASHA Sathi"
          width={153}
          height={50}
          priority
          className="h-auto w-[142px] sm:w-[153px]"
        />
        <div className="hidden items-center gap-2 rounded-full bg-[#eaf8f0] px-4 py-2 text-xs font-bold text-[#167451] sm:flex">
          <span className="size-2 animate-pulse rounded-full bg-[#168457]" />
          Live consultation
        </div>
      </header>

      <div className="grid min-h-0 flex-1 lg:grid-cols-[0.98fr_1.02fr]">
        <section className="relative flex min-h-[430px] flex-col items-center justify-center overflow-hidden border-b border-[#dceee4] bg-[radial-gradient(circle_at_center,#edf9f2_0%,#f7fcf9_47%,#f2fbf6_100%)] px-5 py-10 lg:min-h-0 lg:border-r lg:border-b-0">
          <div className="absolute top-12 -left-16 size-48 rounded-full bg-[#dff4e8]/70 blur-3xl" />
          <div className="absolute -right-16 bottom-4 size-52 rounded-full bg-[#def5e8]/60 blur-3xl" />

          <div
            className={`relative z-10 flex items-center gap-2 rounded-full px-4 py-2 text-xs font-bold ${status.badgeClass}`}
            aria-live="polite"
          >
            <span className="size-2 rounded-full bg-current" />
            {status.label}
          </div>

          <div className="asha-voice-orb relative z-10 mt-7 flex size-64 items-center justify-center sm:size-72">
            <div className="asha-orb-ring asha-orb-ring-one" />
            <div className="asha-orb-ring asha-orb-ring-two" />
            <div className="relative flex size-48 items-center justify-center rounded-full border border-[#d8eee1] bg-white shadow-[0_18px_48px_rgba(22,132,87,0.16)] sm:size-56">
              <div className="absolute flex size-20 items-center justify-center rounded-full bg-[#e7f7ee] text-[#168457] sm:size-24">
                <HeartPulse size={40} strokeWidth={1.8} aria-hidden="true" />
              </div>
              <div className="absolute bottom-7 flex h-10 items-end gap-1.5 sm:bottom-8">
                {WAVE_BARS.map((bar) => (
                  <span
                    key={bar}
                    className="asha-wave-bar w-1.5 rounded-full bg-[#168457]"
                    style={{ animationDelay: `${bar * 100}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-5 text-center">
            <div className="flex items-center justify-center gap-2 text-xl font-extrabold tracking-[-0.025em] text-[#234438]">
              {agentState === 'speaking' ? (
                <Volume2 size={21} aria-hidden="true" />
              ) : (
                <Mic size={20} aria-hidden="true" />
              )}
              {status.title}
            </div>
            <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[#71877d]">
              {status.description}
            </p>
          </div>

          <p className="relative z-10 mt-6 flex items-center gap-2 text-xs text-[#7c9288]">
            <ShieldCheck size={15} aria-hidden="true" />
            Speak naturally in Hindi, English, or Hinglish
          </p>
        </section>

        <section className="flex min-h-[440px] min-w-0 flex-col bg-white lg:min-h-0">
          <div className="flex shrink-0 items-center justify-between border-b border-[#e1efe7] px-5 py-4 sm:px-7">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-[#eaf8f0] text-[#168457]">
                <Activity size={20} aria-hidden="true" />
              </div>
              <div>
                <h1 className="font-bold text-[#244338]">Live conversation</h1>
                <p className="mt-0.5 text-xs text-[#789085]">आपकी बातचीत यहाँ दिखाई देगी</p>
              </div>
            </div>
            <span className="text-xs font-medium text-[#7b9187]">
              {messages.length} {messages.length === 1 ? 'message' : 'messages'}
            </span>
          </div>

          <div className="min-h-0 flex-1 overflow-hidden">
            {messages.length > 0 ? (
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="h-full px-3 py-4 **:data-[slot=message-scroller-content]:p-3 sm:px-5 sm:**:data-[slot=message-scroller-content]:p-5"
              />
            ) : (
              <div className="flex h-full items-center justify-center px-8 text-center">
                <div className="max-w-sm">
                  <div className="mx-auto flex size-16 items-center justify-center rounded-2xl bg-[#ecf9f1] text-[#168457]">
                    <MessageCircleMore size={29} aria-hidden="true" />
                  </div>
                  <h2 className="mt-5 font-bold text-[#2a483b]">
                    Your conversation will appear here
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-[#789085]">
                    बोलना शुरू करें — ASHA Sathi आपकी बात सुनेगी और सहायक सवाल पूछेगी।
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="shrink-0 border-t border-[#e1efe7] bg-[#fbfefc] p-4 sm:px-6 sm:py-5">
            {micError && (
              <div
                role="alert"
                className="mb-3 rounded-xl border border-[#f3c6bf] bg-[#fff5f2] px-4 py-3 text-sm leading-5 text-[#8d3125]"
              >
                <p className="font-bold">Microphone problem</p>
                <p className="mt-1">{micError}</p>
              </div>
            )}
            <AgentControlBar
              variant="livekit"
              controls={{
                microphone: true,
                camera: false,
                screenShare: false,
                chat: false,
                leave: true,
              }}
              isConnected={session.isConnected}
              onDisconnect={session.end}
              onDeviceError={({ source, error }) => {
                console.error('Device error:', error);

                if (source === Track.Source.Microphone) {
                  setMicError(
                    'Microphone access was blocked or is unavailable. Click the lock icon beside the address bar, allow Microphone, then try again.'
                  );
                }
              }}
              className="mx-auto max-w-xl border-[#d5eadd] bg-white shadow-[0_8px_24px_rgba(22,132,87,0.08)]"
            />
            <p className="mt-3 text-center text-[11px] text-[#7c9288]">
              You can end the consultation at any time.
            </p>
          </div>
        </section>
      </div>

      <footer className="shrink-0 border-t border-[#dceee4] bg-white px-5 py-2.5 text-center text-[10px] text-[#7c9288] sm:hidden">
        General health support · Not a replacement for professional medical care
      </footer>
    </main>
  );
}

function getStatus(state: string) {
  switch (state) {
    case 'speaking':
      return {
        label: 'Speaking',
        title: 'ASHA Sathi is speaking',
        description: 'Please listen. You can respond as soon as the guidance is complete.',
        badgeClass: 'bg-[#e6f7ee] text-[#13774e]',
      };
    case 'thinking':
      return {
        label: 'Thinking',
        title: 'ASHA Sathi is thinking',
        description: 'Preparing the next helpful question for you.',
        badgeClass: 'bg-[#fff7df] text-[#8b6812]',
      };
    case 'connecting':
    case 'initializing':
      return {
        label: 'Preparing',
        title: 'Getting ready to listen',
        description: 'Please wait while ASHA Sathi joins the conversation.',
        badgeClass: 'bg-[#eaf3ff] text-[#2d679a]',
      };
    case 'listening':
    case 'idle':
    default:
      return {
        label: 'Listening',
        title: 'Listening to you',
        description: 'अपनी health concern बताइए। ASHA Sathi आपकी सहायता करेगी।',
        badgeClass: 'bg-[#e6f7ee] text-[#13774e]',
      };
  }
}
