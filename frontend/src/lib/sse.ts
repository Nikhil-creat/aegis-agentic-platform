/**
 * WebSocket client hook for streaming live agent thought-logs.
 * Designed and Developed by NIKHIL CHARY SRIRAMOJU
 */
import { useCallback, useRef, useState } from "react";

export interface AgentTraceEvent {
  type: "trace" | "final";
  node?: string;
  data?: unknown[];
  answer?: string;
}

export function useAgentStream(sessionId: string) {
  const [events, setEvents] = useState<AgentTraceEvent[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace("http", "ws") || "ws://localhost:8000";
    const socket = new WebSocket(`${apiUrl}/ws/agent/${sessionId}`);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const payload: AgentTraceEvent = JSON.parse(event.data);
      setEvents((prev) => [...prev, payload]);
      if (payload.type === "final" && payload.answer) {
        setFinalAnswer(payload.answer);
      }
    };

    socketRef.current = socket;
  }, [sessionId]);

  const sendPrompt = useCallback((prompt: string) => {
    socketRef.current?.send(prompt);
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.close();
  }, []);

  return { events, finalAnswer, connected, connect, sendPrompt, disconnect };
}
