"use client";

import { useEffect, useState } from "react";

type SecurityEvent = {
  id: number;
  agent_id: number;
  tool: string;
  risk_score: number;
  decision: string;
  reasons: string[];
  event_type: string;
  message: string | null;
  created_at: string;
};

type DashboardData = {
  summary: {
    total_events: number;
    blocked_events: number;
    approval_events: number;
    allowed_events: number;
    average_risk: number;
  };
  recent_events: SecurityEvent[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://agentshield-qa91.onrender.com";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/dashboard/summary`, {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Backend unavailable");
      }

      const result = await response.json();
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#080808] text-[#f2f2f0] flex items-center justify-center">
        <div className="font-mono text-xs tracking-[0.25em] text-neutral-500">
          INITIALIZING AGENTSHIELD_
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen bg-[#080808] text-[#f2f2f0] flex items-center justify-center">
        <div className="text-center">
          <div className="font-mono text-xs tracking-[0.25em] text-red-500 mb-4">
            SYSTEM ERROR
          </div>

          <h1 className="text-3xl font-semibold tracking-tight">
            SECURITY CORE OFFLINE
          </h1>

          <p className="mt-3 text-sm text-neutral-500">
            Unable to establish connection with AgentShield runtime.
          </p>

          <button
            onClick={loadDashboard}
            className="mt-8 border border-neutral-700 px-6 py-3 font-mono text-xs tracking-wider hover:bg-white hover:text-black transition"
          >
            RETRY CONNECTION
          </button>
        </div>
      </main>
    );
  }

  const { summary, recent_events } = data;

  return (
    <main className="min-h-screen bg-[#080808] text-[#f2f2f0]">
      {/* TOP BAR */}

      <header className="border-b border-[#292927]">
        <div className="max-w-[1500px] mx-auto px-6 lg:px-10 h-[82px] flex items-center justify-between">
          <div className="flex items-center gap-5">
            <div className="w-8 h-8 border border-neutral-600 flex items-center justify-center">
              <div className="w-2 h-2 bg-red-500" />
            </div>

            <div>
              <div className="text-lg font-bold tracking-[-0.04em]">
                AGENTSHIELD
              </div>

              <div className="font-mono text-[9px] tracking-[0.18em] text-neutral-600 mt-1">
                RUNTIME SECURITY INFRASTRUCTURE
              </div>
            </div>
          </div>

          <div className="flex items-center gap-8">
            <div className="hidden md:flex items-center gap-3 font-mono text-[10px] tracking-widest text-neutral-500">
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
              SYSTEM ACTIVE
            </div>

            <button
              onClick={loadDashboard}
              className="border-l border-[#292927] pl-8 font-mono text-[10px] tracking-widest text-neutral-500 hover:text-white transition"
            >
              REFRESH ↻
            </button>
          </div>
        </div>
      </header>

      {/* CONTENT */}

      <div className="max-w-[1500px] mx-auto px-6 lg:px-10">
        {/* HERO */}

        <section className="py-16 border-b border-[#292927]">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-10">
            <div>
              <div className="font-mono text-[10px] tracking-[0.3em] text-red-500 mb-5">
                / SECURITY / OVERVIEW
              </div>

              <h1 className="text-5xl md:text-7xl font-semibold tracking-[-0.065em] leading-[0.9]">
                Runtime
                <br />
                Protection.
              </h1>

              <p className="mt-7 max-w-xl text-sm leading-6 text-neutral-500">
                Autonomous agent actions are evaluated before they reach
                registered tools. Every decision is recorded, scored and
                enforced at runtime.
              </p>
            </div>

            <div className="font-mono text-[10px] text-neutral-600 lg:text-right">
              <div>ENVIRONMENT / DEVELOPMENT</div>
              <div className="mt-2">ENFORCEMENT / ACTIVE</div>
              <div className="mt-2">POLICY ENGINE / ONLINE</div>
              <div className="mt-2">RISK ENGINE / ONLINE</div>
            </div>
          </div>
        </section>

        {/* METRICS */}

        <section className="grid grid-cols-2 lg:grid-cols-5 border-b border-[#292927]">
          <Metric
            label="TOTAL EVENTS"
            value={summary.total_events}
            index="01"
          />

          <Metric
            label="BLOCKED"
            value={summary.blocked_events}
            index="02"
            danger
          />

          <Metric
            label="APPROVAL"
            value={summary.approval_events}
            index="03"
          />

          <Metric
            label="ALLOWED"
            value={summary.allowed_events}
            index="04"
          />

          <Metric
            label="AVG RISK"
            value={summary.average_risk}
            index="05"
          />
        </section>

        {/* EVENTS + SYSTEM */}

        <section className="grid lg:grid-cols-[1fr_360px] border-b border-[#292927]">
          {/* EVENT FEED */}

          <div className="lg:border-r border-[#292927]">
            <div className="h-20 px-6 lg:px-8 flex items-center justify-between border-b border-[#292927]">
              <div>
                <div className="font-mono text-[10px] tracking-[0.2em] text-neutral-500">
                  EVENT STREAM
                </div>

                <div className="text-sm font-medium mt-2">
                  Recent Security Decisions
                </div>
              </div>

              <div className="font-mono text-[10px] text-neutral-600">
                LIVE / {recent_events.length.toString().padStart(2, "0")}
              </div>
            </div>

            {recent_events.map((event, index) => (
              <SecurityEventRow
                key={event.id}
                event={event}
                index={index}
              />
            ))}

            {recent_events.length === 0 && (
              <div className="p-10 text-sm text-neutral-600">
                No security events recorded.
              </div>
            )}
          </div>

          {/* SYSTEM PANEL */}

          <aside>
            <div className="h-20 px-6 flex items-center border-b border-[#292927]">
              <div>
                <div className="font-mono text-[10px] tracking-[0.2em] text-neutral-500">
                  SYSTEM STATUS
                </div>

                <div className="text-sm font-medium mt-2">
                  Enforcement Core
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="border border-[#292927]">
                <div className="p-5 border-b border-[#292927]">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-neutral-500">
                      PROTECTION
                    </span>

                    <span className="flex items-center gap-2 font-mono text-[9px] text-red-500">
                      <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />
                      ACTIVE
                    </span>
                  </div>

                  <div className="text-3xl font-semibold tracking-tight mt-5">
                    ENFORCED
                  </div>
                </div>

                <StatusLine
                  label="POLICY ENGINE"
                  value="ONLINE"
                />

                <StatusLine
                  label="RISK ENGINE"
                  value="ONLINE"
                />

                <StatusLine
                  label="AUDIT LOG"
                  value="ONLINE"
                />

                <StatusLine
                  label="TOOL BOUNDARY"
                  value="ENFORCED"
                />
              </div>

              {/* DISTRIBUTION */}

              <div className="mt-10">
                <div className="font-mono text-[10px] tracking-[0.2em] text-neutral-500 mb-6">
                  DECISION DISTRIBUTION
                </div>

                <Distribution
                  label="BLOCKED"
                  value={summary.blocked_events}
                  total={summary.total_events}
                  danger
                />

                <Distribution
                  label="APPROVAL"
                  value={summary.approval_events}
                  total={summary.total_events}
                />

                <Distribution
                  label="ALLOWED"
                  value={summary.allowed_events}
                  total={summary.total_events}
                />
              </div>
            </div>
          </aside>
        </section>

        {/* FOOTER */}

        <footer className="h-20 flex items-center justify-between font-mono text-[9px] tracking-[0.15em] text-neutral-700">
          <span>AGENTSHIELD / RUNTIME SECURITY</span>

          <span>BUILD 0.1.0</span>
        </footer>
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
  index,
  danger,
}: {
  label: string;
  value: number;
  index: string;
  danger?: boolean;
}) {
  return (
    <div className="h-36 p-5 lg:p-6 border-r border-[#292927] last:border-r-0 relative">
      <div className="flex justify-between">
        <span className="font-mono text-[9px] tracking-[0.2em] text-neutral-600">
          {index}
        </span>

        {danger && value > 0 && (
          <span className="w-1.5 h-1.5 bg-red-500" />
        )}
      </div>

      <div
        className={`text-4xl lg:text-5xl font-semibold tracking-[-0.06em] mt-5 ${
          danger && value > 0 ? "text-red-500" : ""
        }`}
      >
        {value.toString().padStart(2, "0")}
      </div>

      <div className="absolute bottom-5 left-5 lg:left-6 font-mono text-[9px] tracking-[0.18em] text-neutral-600">
        {label}
      </div>
    </div>
  );
}

function SecurityEventRow({
  event,
  index,
}: {
  event: SecurityEvent;
  index: number;
}) {
  const isBlocked = event.decision === "BLOCK";
  const isApproval = event.decision === "REQUIRE_APPROVAL";

  const date = new Date(event.created_at);

  return (
    <article className="px-6 lg:px-8 py-7 border-b border-[#292927] hover:bg-white/[0.02] transition">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
        <div className="flex gap-5">
          <div className="font-mono text-[10px] text-neutral-700 pt-1 w-5">
            {(index + 1).toString().padStart(2, "0")}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-4">
              <span className="font-mono text-xs tracking-wider">
                {event.tool.toUpperCase()}
              </span>

              <span
                className={`font-mono text-[9px] tracking-wider ${
                  isBlocked
                    ? "text-red-500"
                    : isApproval
                      ? "text-neutral-300"
                      : "text-neutral-500"
                }`}
              >
                [{event.decision}]
              </span>
            </div>

            <div className="font-mono text-[9px] text-neutral-700 mt-2">
              AGENT_{event.agent_id.toString().padStart(3, "0")} / EVENT_
              {event.id.toString().padStart(3, "0")}
            </div>
          </div>
        </div>

        <div className="md:text-right">
          <div
            className={`font-mono text-xs ${
              event.risk_score >= 71
                ? "text-red-500"
                : event.risk_score >= 31
                  ? "text-neutral-300"
                  : "text-neutral-500"
            }`}
          >
            RISK {event.risk_score.toString().padStart(3, "0")}
          </div>

          <div className="font-mono text-[9px] text-neutral-700 mt-1">
            {date.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </div>
        </div>
      </div>

      {/* RISK METER */}

      <div className="mt-6 h-[3px] bg-[#20201f]">
        <div
          className={`h-full ${
            event.risk_score >= 71
              ? "bg-red-500"
              : event.risk_score >= 31
                ? "bg-neutral-300"
                : "bg-neutral-600"
          }`}
          style={{
            width: `${Math.max(event.risk_score, 2)}%`,
          }}
        />
      </div>

      {/* REASONS */}

      {event.reasons.length > 0 && (
        <div className="mt-5 grid sm:grid-cols-2 gap-x-8 gap-y-2">
          {event.reasons.map((reason, reasonIndex) => (
            <div
              key={`${event.id}-${reasonIndex}`}
              className="flex items-start gap-3 font-mono text-[9px] leading-5 text-neutral-600"
            >
              <span className="text-neutral-800">
                {reasonIndex.toString().padStart(2, "0")}
              </span>

              <span>{reason.toUpperCase()}</span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function StatusLine({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="px-5 py-4 border-b border-[#292927] last:border-b-0 flex items-center justify-between">
      <span className="font-mono text-[9px] tracking-wider text-neutral-600">
        {label}
      </span>

      <span className="font-mono text-[9px] tracking-wider text-neutral-400">
        {value}
      </span>
    </div>
  );
}

function Distribution({
  label,
  value,
  total,
  danger,
}: {
  label: string;
  value: number;
  total: number;
  danger?: boolean;
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div className="mb-7">
      <div className="flex justify-between mb-3">
        <span className="font-mono text-[9px] tracking-wider text-neutral-600">
          {label}
        </span>

        <span
          className={`font-mono text-[9px] ${
            danger && value > 0 ? "text-red-500" : "text-neutral-500"
          }`}
        >
          {value.toString().padStart(2, "0")} /{" "}
          {percentage.toFixed(0).padStart(3, " ")}%
        </span>
      </div>

      <div className="h-[2px] bg-[#20201f]">
        <div
          className={`h-full ${danger ? "bg-red-500" : "bg-neutral-500"}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}