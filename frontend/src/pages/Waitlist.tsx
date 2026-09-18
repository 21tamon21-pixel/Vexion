import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { ArrowRight, Check, ShieldCheck, Sparkles, TimerReset } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { apiPost } from "@/lib/api";
import { useAppConfig } from "@/hooks/useAuth";
import type { WaitlistResponse } from "@/types";

export default function Waitlist() {
  const navigate = useNavigate();
  const { data: config } = useAppConfig();
  const [email, setEmail] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<WaitlistResponse | null>(null);
  const [error, setError] = useState("");

  const releaseDate = config?.beta.release_date ? new Date(config.beta.release_date) : null;

  const countdown = useMemo(() => {
    if (!releaseDate || Number.isNaN(releaseDate.getTime())) return null;
    const diffMs = releaseDate.getTime() - Date.now();
    if (diffMs <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0 };
    const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
    return {
      days: Math.floor(totalSeconds / 86400),
      hours: Math.floor((totalSeconds % 86400) / 3600),
      minutes: Math.floor((totalSeconds % 3600) / 60),
      seconds: totalSeconds % 60,
    };
  }, [releaseDate]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!agreed) {
      setError("Please review and accept the terms before joining.");
      return;
    }
    setSubmitting(true);
    try {
      const response = await apiPost<WaitlistResponse>("/waitlist", { email });
      setResult(response);
      localStorage.setItem("vexion.beta-joined", "true");
    } catch {
      setError("Please enter a valid email address and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6f3ee] px-4 py-6 text-[#1d1c1a] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#1d1c1a]">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#b8552f] text-xs font-bold text-white">V</span>
            VEXION
          </Link>
          <Link to="/chat" className="rounded-full border border-[#e6ddd5] bg-white/80 px-4 py-2 text-sm font-medium text-[#3d3b37] shadow-sm transition hover:bg-white">
            Open workspace
          </Link>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-[2rem] border border-[#e6ddd5] bg-white p-6 shadow-[0_25px_70px_rgba(60,41,28,0.08)] sm:p-8 lg:p-10">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#f0d3c1] bg-[#fff5f0] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#9a4827]">
              <Sparkles className="h-3.5 w-3.5" /> Early access
            </div>

            <h1 className="max-w-xl font-heading text-4xl leading-none tracking-[-0.06em] text-[#1d1c1a] sm:text-5xl lg:text-6xl">
              Meet VEXION.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-[#5d5a54] sm:text-lg">
              A calmer, faster way to build, reason and ship code with VEX AI — all in one workspace designed for focus.
            </p>

            {releaseDate && countdown && (
              <div className="mt-8 grid max-w-lg gap-3 sm:grid-cols-4">
                {[
                  { label: "Days", value: countdown.days },
                  { label: "Hours", value: countdown.hours },
                  { label: "Minutes", value: countdown.minutes },
                  { label: "Seconds", value: countdown.seconds },
                ].map((item) => (
                  <div key={item.label} className="rounded-2xl border border-[#e6ddd5] bg-[#f9f5f1] p-3 text-center">
                    <div className="text-2xl font-semibold tracking-[-0.05em] text-[#1d1c1a]">{String(item.value).padStart(2, "0")}</div>
                    <div className="mt-1 text-[10px] uppercase tracking-[0.18em] text-[#625d58]">{item.label}</div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-8 flex flex-wrap items-center gap-4 text-sm text-[#494642]">
              <span className="inline-flex items-center gap-2 rounded-full border border-[#e6ddd5] bg-[#f8f5f1] px-3 py-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-[#3f6b45]" /> Anonymous beta access
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-[#e6ddd5] bg-[#f8f5f1] px-3 py-1.5">
                <TimerReset className="h-3.5 w-3.5 text-[#b8552f]" /> VEX AI only
              </span>
            </div>
          </section>

          <aside className="rounded-[2rem] border border-[#e6ddd5] bg-[#1d1c1a] p-6 text-white shadow-[0_22px_60px_rgba(20,16,13,0.2)] sm:p-8">
            {!result ? (
              <>
                <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f3c4a7]">Join beta</p>
                <h2 className="mt-4 font-heading text-3xl tracking-[-0.05em] text-white">Early access starts here.</h2>
                <p className="mt-3 text-sm leading-relaxed text-[#d1cac3]">
                  Join the queue and we’ll email you when VEXION is ready for your invite.
                </p>

                <form onSubmit={submit} className="mt-6 space-y-4">
                  <label className="block">
                    <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#d1cac3]">Email address</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                      placeholder="you@example.com"
                      className="w-full rounded-2xl border border-[#3a3733] bg-[#272420] px-4 py-3.5 text-sm text-white outline-none transition focus:border-[#d98060]"
                    />
                  </label>

                  <label className="flex items-start gap-3 rounded-2xl border border-[#3a3733] bg-[#272420] p-3 text-left text-xs leading-relaxed text-[#d1cac3]">
                    <input
                      type="checkbox"
                      checked={agreed}
                      onChange={(event) => setAgreed(event.target.checked)}
                      className="mt-0.5 h-4 w-4 accent-[#b8552f]"
                    />
                    <span>
                      I agree to receive early-access updates and accept the VEXION beta terms and privacy notice.
                    </span>
                  </label>

                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#b8552f] px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-[#9f4829] disabled:opacity-60"
                  >
                    {submitting ? "Joining…" : "Join Early Access"}
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </form>

                {error && <p className="mt-3 text-sm text-[#f5b5a5]">{error}</p>}
              </>
            ) : (
              <div className="py-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ebf6ee] text-[#3f6b45]">
                  <Check className="h-5 w-5" />
                </div>
                <p className="mt-5 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#d1cac3]">You&apos;re in</p>
                <h3 className="mt-3 font-heading text-4xl tracking-[-0.06em] text-white">#{result.position.toLocaleString()}</h3>
                <p className="mt-3 text-sm leading-relaxed text-[#d1cac3]">{result.message}</p>
                <button
                  onClick={() => navigate("/chat")}
                  className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-[#1d1c1a] transition hover:bg-[#f1eee9]"
                >
                  Open VEXION <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </aside>
        </div>
      </div>
    </main>
  );
}
