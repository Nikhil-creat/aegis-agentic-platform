/**
 * CodeRunner — submits code to the sandboxed polyglot execution engine and
 * displays stdout/stderr and timing.
 *
 * Designed and Developed by NIKHIL CHARY SRIRAMOJU
 */
"use client";

import { useState } from "react";

const LANGUAGES = ["python", "javascript", "java", "c", "shell", "html", "reactjs"];

interface ExecResult {
  job_id: string;
  success: boolean;
  output: string;
  error: string | null;
  duration_seconds: number;
}

export default function CodeRunner({ token }: { token: string }) {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState('print("Hello from Aegis sandbox")');
  const [result, setResult] = useState<ExecResult | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/execute/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ language, code }),
      });
      setResult(await res.json());
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-700 bg-slate-900 p-6 text-slate-100">
      <h2 className="text-lg font-semibold">Secure Polyglot Code Runner</h2>

      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="w-40 rounded-md bg-slate-800 px-2 py-1 text-sm"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang} value={lang}>
            {lang}
          </option>
        ))}
      </select>

      <textarea
        className="h-40 rounded-md bg-slate-950 p-3 font-mono text-sm outline-none"
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />

      <button
        onClick={run}
        disabled={loading}
        className="w-32 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
      >
        {loading ? "Running..." : "Execute"}
      </button>

      {result && (
        <pre
          className={`whitespace-pre-wrap rounded-md p-3 text-xs ${
            result.success ? "bg-emerald-950/40 text-emerald-300" : "bg-rose-950/40 text-rose-300"
          }`}
        >
          {result.output || result.error}
          {"\n"}— {result.duration_seconds}s (job {result.job_id})
        </pre>
      )}
    </div>
  );
}
