import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { randomUUID } from 'crypto';
import {
  AccessToken,
  type AccessTokenOptions,
  type VideoGrant,
} from 'livekit-server-sdk';
import { RoomConfiguration } from '@livekit/protocol';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// Environment variables from .env.local
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const AGENT_NAME = process.env.AGENT_NAME;

// Don't cache the results
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }

    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }

    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Parse room config from request body (if provided)
    const body = await req.json().catch(() => ({}));

    let roomConfig: RoomConfiguration | undefined;

    if (body?.room_config) {
      roomConfig = RoomConfiguration.fromJson(body.room_config, {
        ignoreUnknownFields: true,
      });
    } else if (AGENT_NAME) {
      // Configure explicit agent dispatch when AGENT_NAME is set
      roomConfig = RoomConfiguration.fromJson(
        { agents: [{ agentName: AGENT_NAME }] },
        { ignoreUnknownFields: true }
      );
    }

    // ---------------------------------------------------------
    // Persistent ASHA Sathi user identity
    // ---------------------------------------------------------
    const cookieStore = await cookies();

    let userId = cookieStore.get('asha_sathi_user_id')?.value;

    if (!userId) {
      userId = `asha_${randomUUID()}`;

      cookieStore.set('asha_sathi_user_id', userId, {
        httpOnly: true,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24 * 365, // 1 year
        path: '/',
      });
    }

    // Participant identity stays the same across calls
    // while the room name remains temporary.
    const participantName = 'user';
    const participantIdentity = userId;
    const roomName = `voice_assistant_room_${Math.floor(
      Math.random() * 10_000
    )}`;

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
      },
      roomName,
      roomConfig
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName,
      participantToken,
    };

    const headers = new Headers({
      'Cache-Control': 'no-store',
    });

    return NextResponse.json(data, { headers });
  } catch (error) {
    console.error(error);

    const message =
      error instanceof Error ? error.message : 'Internal server error';

    return new NextResponse(message, { status: 500 });
  }
}

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string,
  roomConfig?: RoomConfiguration
): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '15m',
  });

  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };

  at.addGrant(grant);

  if (roomConfig) {
    at.roomConfig = roomConfig;
  }

  return at.toJwt();
}