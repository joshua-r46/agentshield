"use client";

import { useState } from "react";
import Dashboard from "./Dashboard";

type View = "dashboard" | "api" | "demo";

export default function Home() {
  const [view, setView] = useState<View>("dashboard");

  return (
    <main className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">

      {/* APP */}
      <div className="min-h-screen pb-24">

        {view === "dashboard" && <Dashboard />}

        {view === "api" && (
          <section className="h-[calc(100vh-96px)] p-4 md:p-6">
            <div className="h-full overflow-hidden rounded-[24px] border border-black/10 bg-white shadow-sm">
              <iframe
                src={`${process.env.NEXT_PUBLIC_API_URL}/docs`}
                title="AgentShield Security API"
                className="h-full w-full border-0"
              />
            </div>
          </section>
        )}

        {view === "demo" && (
          <section className="min-h-[calc(100vh-96px)] p-6 md:p-10">
            <div className="mx-auto max-w-6xl">

              <div className="mb-10">
                <p className="text-sm font-medium text-[#86868b]">
                  AGENTSHIELD
                </p>

                <h1 className="mt-2 text-4xl font-semibold tracking-tight md:text-6xl">
                  Runtime Security
                </h1>

                <p className="mt-4 max-w-2xl text-lg text-[#86868b]">
                  Autonomous agent actions are evaluated before reaching
                  registered tools.
                </p>
              </div>

              <div className="grid gap-5 md:grid-cols-3">

                <DemoCard
                  number="01"
                  title="Agent proposes"
                  description="The agent requests a tool action."
                />

                <DemoCard
                  number="02"
                  title="AgentShield evaluates"
                  description="Policy, permissions, risk, consequence and behavior are evaluated."
                />

                <DemoCard
                  number="03"
                  title="Decision enforced"
                  description="ALLOW, REQUIRE APPROVAL or BLOCK is enforced at the tool boundary."
                />

              </div>

              <div className="mt-6 rounded-[28px] border border-black/10 bg-white p-8 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium tracking-widest text-[#86868b]">
                      SECURITY BOUNDARY
                    </p>

                    <h2 className="mt-3 text-2xl font-semibold">
                      Agent → AgentShield → Tool
                    </h2>
                  </div>

                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-black text-white">
                    ✓
                  </div>
                </div>

                <div className="mt-8 grid gap-3 md:grid-cols-3">
                  <FlowItem text="UNTRUSTED ACTION" />
                  <FlowItem text="RISK EVALUATION" />
                  <FlowItem text="ENFORCED DECISION" />
                </div>
              </div>

            </div>
          </section>
        )}

      </div>

      {/* BOTTOM NAVIGATION */}
      <nav className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
        <div className="flex items-center gap-1 rounded-full border border-black/10 bg-white/90 p-1.5 shadow-[0_12px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl">

          <NavButton
            active={view === "dashboard"}
            onClick={() => setView("dashboard")}
          >
            Dashboard
          </NavButton>

          <NavButton
            active={view === "api"}
            onClick={() => setView("api")}
          >
            Security API
          </NavButton>

          <NavButton
            active={view === "demo"}
            onClick={() => setView("demo")}
          >
            Demo
          </NavButton>

        </div>
      </nav>

    </main>
  );
}

function NavButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-5 py-2.5 text-sm font-medium transition-all ${
        active
          ? "bg-[#1d1d1f] text-white shadow-sm"
          : "text-[#6e6e73] hover:bg-[#f2f2f2] hover:text-[#1d1d1f]"
      }`}
    >
      {children}
    </button>
  );
}

function DemoCard({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[24px] border border-black/10 bg-white p-7 shadow-sm">
      <div className="text-xs font-medium text-[#86868b]">
        {number}
      </div>

      <h3 className="mt-8 text-xl font-semibold">
        {title}
      </h3>

      <p className="mt-3 text-sm leading-6 text-[#86868b]">
        {description}
      </p>
    </div>
  );
}

function FlowItem({ text }: { text: string }) {
  return (
    <div className="rounded-2xl bg-[#f5f5f7] px-5 py-4 text-center text-xs font-medium tracking-wide text-[#6e6e73]">
      {text}
    </div>
  );
}