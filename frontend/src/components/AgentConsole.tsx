/**
 * AgentConsole — live-streaming chat UI for the Aegis agent graph.
 * Renders each node's trace event as it arrives over the WebSocket, then
 * the final answer once the graph reaches the `finalize` node.
 *
 * Designed and Developed by NIKHIL CHARY SRIRAMOJU
 */
"use client";

import { useState } from "react";
import { useAgentStream } from "../lib/sse";

export default function AgentConsole({ sessionId }: { sessionId: string }) {
  const { events, finalAnswer, connected, connect, sendPrompt, disconnect } = useAgentStream(sessionId);
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    if (!connected) connect();
    setTimeout(() => sendPrompt(prompt), 300); // allow socket handshake
  };

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-100">
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Aegis Agent Console</h2>
        <span className={`text-xs ${connected ? "text-emerald-400" : "text-slate-500"}`}>
          {connected ? "● connected" : "○ disconnected"}
        </span>
      </header>

      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md bg-slate-800 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Ask Aegis to plan, retrieve, or run code..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        />
        <button
          onClick={handleSubmit}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500"
        >
          Run
        </button>
        <button onClick={disconnect} className="rounded-md bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600">
          Stop
        </button>
      </div>

      <div className="max-h-96 space-y-2 overflow-y-auto rounded-md bg-slate-950 p-3 font-mono text-xs">
        {events.map((event, idx) => (
          <div key={idx} className="border-b border-slate-800 pb-1">
            <span className="text-indigo-400">[{event.node ?? event.type}]</span>{" "}
            <span className="text-slate-300">{JSON.stringify(event.data ?? event.answer)}</span>
          </div>
        ))}
      </div>

      {finalAnswer && (
        <div className="rounded-md border border-emerald-700 bg-emerald-950/40 p-3 text-sm">
          <strong className="text-emerald-400">Final Answer:</strong> {finalAnswer}
        </div>
      )}

      <footer className="pt-2 text-center text-[11px] text-slate-600">
        Aegis Autonomous Agentic Platform — Designed and Developed by NIKHIL CHARY SRIRAMOJU
      </footer>
    </div>
  );
}
