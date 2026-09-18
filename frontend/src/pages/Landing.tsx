import { useState } from "react";
import type { FormEvent } from "react";
import { ArrowRight, Check, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { apiPost } from "@/lib/api";
import { useAppConfig } from "@/hooks/useAuth";
import type { WaitlistResponse } from "@/types";

export default function Landing() {
  const navigate = useNavigate();
  const { data: config } = useAppConfig();
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<WaitlistResponse | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await apiPost<WaitlistResponse>("/waitlist", { email });
      setResult(response);
      localStorage.setItem("vexion.beta-joined", "true");
    } catch {
      setError("Enter a valid email address and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-background px-6 py-8 text-foreground">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col">
        <header className="flex items-center justify-between">
          <button onClick={() => navigate("/chat")} className="font-heading text-xl font-semibold tracking-tight">
            VEXION
          </button>
          <button
            onClick={() => navigate("/chat")}
            className="rounded-full border border-border px-4 py-2 text-sm text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          >
            Open workspace
          </button>
        </header>

        <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.1fr_.9fr]">
          <div className="max-w-2xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#e4c9ba] bg-[#fff7f2] px-3 py-1.5 text-xs font-medium text-[#9a4827]">
              <Sparkles className="h-3.5 w-3.5" /> {config?.beta.status === "open" ? "Beta is open" : "Early access"}
            </div>
            <h1 className="font-heading text-5xl leading-[1.02] tracking-tight md:text-7xl">
              Build with a sharper kind of calm.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
              VEXION is a coding-first AI workspace for thinking through problems, writing code and shipping useful things with VEX AI.
            </p>
            {config?.beta.release_date && (
              <p className="mt-4 text-sm text-muted-foreground">Beta opens {config.beta.release_date}.</p>
            )}
          </div>

          <div className="rounded-[2rem] border border-border bg-card p-6 shadow-[0_18px_60px_rgba(74,53,40,0.09)] md:p-8">
            {!result ? (
              <>
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#b8552f]">Join the VEXION Beta</p>
                <h2 className="mt-3 font-heading text-3xl tracking-tight">Early access, without the ceremony.</h2>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  Leave your email for release updates, then open the workspace immediately to try VEX AI.
                </p>
                <form onSubmit={submit} className="mt-7 space-y-3">
                  <input
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    type="email"
                    required
                    placeholder="you@example.com"
                    aria-label="Email address"
                    className="w-full rounded-2xl border border-border bg-background px-4 py-3.5 text-sm outline-none transition focus:border-[#b8552f]"
                  />
                  <button
                    disabled={submitting}
                    className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#b8552f] px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-[#9f4829] disabled:opacity-60"
                  >
                    {submitting ? "Joining…" : "Join Early Access"} <ArrowRight className="h-4 w-4" />
                  </button>
                </form>
                {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
              </>
            ) : (
              <div className="py-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#e8f0e6] text-[#3f6b45]"><Check className="h-5 w-5" /></div>
                <p className="mt-6 text-sm font-semibold uppercase tracking-[0.16em] text-[#3f6b45]">You&apos;re in</p>
                <h2 className="mt-3 font-heading text-4xl tracking-tight">Position #{result.position.toLocaleString()}</h2>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{result.message}</p>
                <button onClick={() => navigate("/chat")} className="mt-8 flex items-center gap-2 rounded-2xl bg-[#b8552f] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#9f4829]">Open VEXION <ArrowRight className="h-4 w-4" /></button>
              </div>
            )}
          </div>
        </section>

        <footer className="flex flex-wrap gap-5 border-t border-border py-5 text-xs text-muted-foreground">
          <span>VEX AI</span><span>10,000 weekly credits</span><span>Anonymous by default</span><span>{config?.beta.message ?? "A focused AI workspace for building and shipping code."}</span>
        </footer>
      </div>
    </main>
  );
}
