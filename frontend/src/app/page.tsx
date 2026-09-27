/**
 * Aegis Dashboard — home page.
 * Designed and Developed by NIKHIL CHARY SRIRAMOJU
 */
import AgentConsole from "../components/AgentConsole";
import CodeRunner from "../components/CodeRunner";

export default function HomePage() {
  const sessionId = crypto.randomUUID();

  return (
    <main className="min-h-screen bg-slate-950 p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <h1 className="text-2xl font-bold text-white">Aegis Autonomous Agentic Platform</h1>
        <p className="text-sm text-slate-400">
          Designed and Developed by <span className="text-indigo-400">NIKHIL CHARY SRIRAMOJU</span>
        </p>
        <AgentConsole sessionId={sessionId} />
        <CodeRunner token="" />
      </div>
    </main>
  );
}
