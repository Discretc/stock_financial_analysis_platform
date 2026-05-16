/**
 * WebSocket hook for real-time price streaming.
 *
 * Protocol (matches backend/app/api/v1/websocket.py):
 *   Server → client:
 *     { type: 'price', data: StockQuote, timestamp: string }
 *     { type: 'pong', timestamp: string }
 *     { type: 'error', message: string }
 *   Client → server:
 *     { type: 'ping' }
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { StockQuote } from '@/types/stock';

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  enabled?: boolean;
  onQuote?: (quote: StockQuote) => void;
}

export function useWebSocket(ticker: string, options: UseWebSocketOptions = {}) {
  const { enabled = true, onQuote } = options;
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef(true);

  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_BASE_DELAY_MS = 1_000;

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!ticker || !enabled || !isMountedRef.current) return;

    const wsUrl =
      typeof window !== 'undefined'
        ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/ws/stocks/${ticker}`
        : null;

    if (!wsUrl) return;

    setConnectionState('connecting');

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      setConnectionState('connected');
      reconnectAttemptsRef.current = 0;

      // Start client-side heartbeat (ping every 25s to keep connection alive)
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25_000);
    };

    ws.onmessage = (event: MessageEvent) => {
      if (!isMountedRef.current) return;
      try {
        const msg = JSON.parse(event.data as string) as {
          type: string;
          data?: StockQuote;
          message?: string;
        };
        if (msg.type === 'price' && msg.data) {
          setQuote(msg.data);
          onQuote?.(msg.data);
        }
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!isMountedRef.current) return;
      clearTimers();
      setConnectionState('disconnected');

      // Exponential backoff reconnect
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay =
          RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      } else {
        setConnectionState('error');
      }
    };

    ws.onerror = () => {
      if (!isMountedRef.current) return;
      setConnectionState('error');
      ws.close();
    };
  }, [ticker, enabled, onQuote, clearTimers]);

  useEffect(() => {
    isMountedRef.current = true;
    if (enabled && ticker) connect();

    return () => {
      isMountedRef.current = false;
      clearTimers();
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [ticker, enabled, connect, clearTimers]);

  return { quote, connectionState };
}
