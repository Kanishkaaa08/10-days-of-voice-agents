'use client';

import {
  useAgent,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';

import { Heart, ShieldCheck, Mic, PhoneDisconnect } from '@phosphor-icons/react/dist/ssr';

import type { AppConfig } from '@/app-config';

import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';

import { AgentControlBar } from '@/components/agents-ui/agent-control-bar';

import { AudioVisualizer } from '@/components/agents-ui/blocks/agent-session-view-01/components/audio-visualizer';

interface SessionViewProps {
  appConfig: AppConfig;
}

export function SessionView({ appConfig }: SessionViewProps) {
  const session = useSessionContext();

  const { state: agentState } = useAgent();

  const { messages } = useSessionMessages(session);

  const status = getStatus(agentState);

  return (
    <main className="min-h-svh bg-[#F5FBF8] px-4 py-4 md:px-8 md:py-6">
      <div className="mx-auto flex min-h-[calc(100svh-2rem)] max-w-7xl flex-col overflow-hidden rounded-[28px] border border-emerald-100 bg-white shadow-[0_20px_70px_rgba(22,133,91,0.10)] md:min-h-[calc(100svh-3rem)]">

        {/* HEADER */}
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-4 md:px-7">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
              <Heart weight="fill" size={23} />
            </div>

            <div>
              <h1 className="text-base font-bold text-slate-900">
                ASHA Sathi
              </h1>

              <p className="text-xs text-slate-500">
                आपकी स्वास्थ्य सहायता साथी
              </p>
            </div>
          </div>

          <div
            className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ${status.className}`}
          >
            <span className="size-2 rounded-full bg-current" />
            {status.label}
          </div>
        </header>

        {/* BODY */}
        <div className="grid min-h-0 flex-1 lg:grid-cols-[0.9fr_1.1fr]">

          {/* LEFT - AGENT */}
          <section className="flex flex-col items-center justify-center border-b border-slate-100 bg-linear-to-b from-[#F5FBF8] to-white px-5 py-8 lg:border-r lg:border-b-0">

            <div className="mb-5 flex items-center gap-2 rounded-full bg-white px-4 py-2 text-xs font-medium text-slate-600 shadow-sm ring-1 ring-emerald-100">
              <ShieldCheck
                size={17}
                weight="fill"
                className="text-emerald-600"
              />
              Healthcare support for ASHA workers
            </div>

            <div className="relative flex h-[280px] w-full max-w-[430px] items-center justify-center md:h-[340px]">

              <div className="absolute size-[230px] rounded-full bg-emerald-100/40 blur-3xl" />

              <AudioVisualizer
                isChatOpen={false}
                audioVisualizerType={appConfig.audioVisualizerType ?? 'bar'}
                audioVisualizerColor={appConfig.audioVisualizerColor}
                audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
                audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
                audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
                audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
                audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
                audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
                audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
              />
            </div>

            <div className="mt-2 text-center">
              <h2 className="text-xl font-bold text-slate-900">
                {status.title}
              </h2>

              <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                {status.description}
              </p>
            </div>

            <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
              <Mic size={15} />
              Speak naturally in Hindi, English or Hinglish
            </div>
          </section>

          {/* RIGHT - TRANSCRIPT */}
          <section className="flex min-h-0 flex-1 flex-col bg-white">

            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4 md:px-6">
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Live Conversation
                </h2>

                <p className="mt-0.5 text-xs text-slate-400">
                  आपकी बातचीत यहाँ दिखाई देगी
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-emerald-600">
                <span className="size-2 animate-pulse rounded-full bg-emerald-500" />
                Live
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-hidden">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center px-8 text-center">
                  <div className="max-w-sm">
                    <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                      <Mic size={26} weight="fill" />
                    </div>

                    <h3 className="font-semibold text-slate-800">
                      I’m listening
                    </h3>

                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      Start speaking about the patient or health concern.
                      Your conversation will appear here.
                    </p>
                  </div>
                </div>
              ) : (
                <AgentChatTranscript
                  agentState={agentState}
                  messages={messages}
                  className="h-full **:data-[slot=message-scroller-content]:p-5 md:**:data-[slot=message-scroller-content]:p-6"
                />
              )}
            </div>

            {/* CONTROLS */}
            <div className="border-t border-slate-100 bg-[#FAFCFB] p-4 md:p-5">
              <AgentControlBar
                variant="livekit"
                isConnected={session.isConnected}
                controls={{
                  microphone: true,
                  leave: true,
                  camera: false,
                  screenShare: false,
                  chat: false,
                }}
                onDisconnect={session.end}
                onDeviceError={({ source, error }) => {
                  if (source === 'microphone') {
                    console.error('Microphone error:', error);
                  }
                }}
                className="mx-auto max-w-xl border-emerald-100 bg-white shadow-sm"
              />

              <p className="mt-3 text-center text-[11px] text-slate-400">
                You can end the consultation anytime.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

function getStatus(state: string) {
  switch (state) {
    case 'speaking':
      return {
        label: 'Speaking',
        title: 'ASHA Sathi is speaking',
        description:
          'Listen to the guidance. You can speak again when the response is complete.',
        className: 'bg-emerald-50 text-emerald-700',
      };

    case 'thinking':
      return {
        label: 'Thinking',
        title: 'ASHA Sathi is thinking',
        description:
          'Processing the information you shared...',
        className: 'bg-amber-50 text-amber-700',
      };

    case 'listening':
    case 'idle':
    default:
      return {
        label: 'Listening',
        title: 'I’m listening',
        description:
          'Tell me about the patient or health concern you want help with.',
        className: 'bg-emerald-50 text-emerald-700',
      };
  }
}