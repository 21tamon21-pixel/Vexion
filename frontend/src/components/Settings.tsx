import { X } from "lucide-react";
import { generateApiKey } from "../lib/api";
import { useState } from "react";

type Props = {
  onClose: () => void;
};

export default function Settings({ onClose }: Props) {
  const [generatedKey, setGeneratedKey] = useState("");
  const [error, setError] = useState("");

  async function createKey() {
    setError("");

    try {
      const result = await generateApiKey();
      setGeneratedKey(result.key);
    } catch {
      setError("Could not generate the API key.");
    }
  }

  return (
    <div className="settings-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <div>
            <div className="settings-title">Settings</div>
            <div className="settings-subtitle">
              Configure your VEXION workspace.
            </div>
          </div>

          <button className="close-button" onClick={onClose}>
            <X size={19} />
          </button>
        </div>

        <section className="settings-section">
          <h3>VEXION API</h3>

          <p>
            Generate an API key for applications that will connect to VEXION.
          </p>

          <button className="primary-button" onClick={createKey}>
            Generate API key
          </button>

          {generatedKey && (
            <div className="generated-key">
              <div className="generated-key-warning">
                Save this key now. It will not be shown again.
              </div>

              <code>{generatedKey}</code>
            </div>
          )}

          {error && <div className="error-text">{error}</div>}
        </section>

        <section className="settings-section">
          <h3>About</h3>
          <p>VEXION 1.0 — free AI workspace.</p>
        </section>
      </div>
    </div>
  );
}
