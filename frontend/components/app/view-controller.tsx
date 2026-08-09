'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { ConnectionState } from 'livekit-client';
import { LoaderCircle, ShieldCheck } from 'lucide-react';
import { useConnectionState, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { SessionView } from '@/components/app/session-view';
import { WelcomeView } from '@/components/app/welcome-view';

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const connectionState = useConnectionState(session.room);
  const [hasConnected, setHasConnected] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    if (connectionState === ConnectionState.Connected) {
      setHasConnected(true);
      setIsStarting(false);
      setStartError(null);
    }

    if (connectionState === ConnectionState.Disconnected) {
      setIsStarting(false);
    }
  }, [connectionState]);

  const handleStartCall = async () => {
    setStartError(null);
    setHasConnected(false);
    setIsStarting(true);

    try {
      await session.start();
    } catch (error) {
      console.error('Unable to start ASHA Sathi:', error);

      const errorName = error instanceof DOMException ? error.name : '';
      const errorMessage = error instanceof Error ? error.message : '';
      const microphoneWasBlocked =
        errorName === 'NotAllowedError' ||
        errorName === 'PermissionDeniedError' ||
        /permission|microphone|not.?allowed/i.test(errorMessage);

      setStartError(
        microphoneWasBlocked
          ? 'Your browser blocked the microphone. Click the lock icon beside the address bar, open Site settings, set Microphone to Allow, then try again.'
          : 'We could not connect right now. Please check your internet connection and try again.'
      );
      setIsStarting(false);
    }
  };

  if (
    isStarting ||
    connectionState === ConnectionState.Connecting ||
    connectionState === ConnectionState.Reconnecting
  ) {
    return <ConnectingView reconnecting={connectionState === ConnectionState.Reconnecting} />;
  }

  if (connectionState === ConnectionState.Connected) {
    return <SessionView />;
  }

  return (
    <WelcomeView
      startButtonText={hasConnected ? 'Start a new consultation' : appConfig.startButtonText}
      onStartCall={handleStartCall}
      errorMessage={startError}
      ended={hasConnected}
      isStarting={isStarting}
    />
  );
}

function ConnectingView({ reconnecting }: { reconnecting: boolean }) {
  return (
    <main className="flex min-h-svh items-center justify-center bg-[#f2fbf6] px-5">
      <div className="relative w-full max-w-md overflow-hidden rounded-[30px] border border-[#dceee4] bg-white p-8 text-center shadow-[0_24px_70px_rgba(19,94,63,0.13)] sm:p-10">
        <div className="absolute -top-20 -right-20 size-48 rounded-full bg-[#e2f7eb] blur-2xl" />
        <Image
          src="/image.png"
          alt="ASHA Sathi"
          width={153}
          height={50}
          priority
          className="relative mx-auto h-auto w-[153px]"
        />
        <div className="relative mx-auto mt-9 flex size-20 items-center justify-center rounded-full bg-[#e8f8ef] text-[#168457]">
          <LoaderCircle className="size-9 animate-spin" aria-hidden="true" />
        </div>
        <p className="relative mt-7 text-sm font-bold tracking-[0.14em] text-[#197451] uppercase">
          {reconnecting ? 'Reconnecting' : 'ASHA Sathi'}
        </p>
        <h1 className="relative mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[#19392c]">
          {reconnecting ? 'Restoring your call…' : 'Connecting…'}
        </h1>
        <p className="relative mt-4 text-base leading-7 text-[#71877d]">
          आपकी स्वास्थ्य सहायता साथी से जुड़ रहे हैं।
          <br />
          Please wait a moment.
        </p>
        <p className="relative mt-7 flex items-center justify-center gap-2 text-xs text-[#7c9288]">
          <ShieldCheck size={15} aria-hidden="true" />
          Your health conversation stays private
        </p>
      </div>
    </main>
  );
}
