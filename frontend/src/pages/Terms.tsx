import { Link } from "react-router-dom";

export default function Terms() {
  return (
    <main className="min-h-screen bg-[#f6f3ee] px-4 py-8 text-[#1d1c1a] sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-[2rem] border border-[#e6ddd5] bg-white p-6 shadow-[0_20px_60px_rgba(57,42,29,0.07)] sm:p-8">
        <Link to="/" className="inline-flex items-center text-sm font-medium text-[#3d3b37] underline decoration-[#b8552f] underline-offset-4">
          ← Back to VEXION
        </Link>

        <h1 className="mt-6 font-heading text-4xl tracking-[-0.06em]">Terms & privacy</h1>

        <div className="mt-6 space-y-4 text-sm leading-relaxed text-[#57534e]">
          <p>
            VEXION beta is a private early-access product. Participation is by invitation and we may update availability, queue position and access timing at any time.
          </p>
          <p>
            We collect only the information needed to manage beta access, including your email address and queue position. This data is stored in the existing VEXION backend storage and used for release communications only.
          </p>
          <p>
            Anonymous usage, chat history and credits are kept server-side. Provider API keys and infrastructure secrets are never exposed to the browser.
          </p>
          <p>
            VEXION may be updated or paused during beta. We do not sell personal information. For the product to work, anonymous usage and queue metadata may be stored locally and on the backend.
          </p>
        </div>
      </div>
    </main>
  );
}
