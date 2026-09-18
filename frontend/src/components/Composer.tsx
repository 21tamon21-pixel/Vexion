import {
  ArrowUp,
  Paperclip,
  Plus,
  Sparkles,
} from "lucide-react";
import ModelPicker from "./ModelPicker";
import type { ModelInfo } from "@/types";

type Props = {
  value: string;
  setValue: (value: string) => void;
  models: ModelInfo[];
  selectedModel: string;
  setSelectedModel: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
};

export default function Composer({
  value,
  setValue,
  models,
  selectedModel,
  setSelectedModel,
  onSend,
  disabled,
}: Props) {
  function submit() {
    if (!value.trim() || disabled) return;
    onSend();
  }

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder="Message VEXION..."
          rows={1}
        />

        <div className="composer-bottom">
          <div className="composer-tools">
            <button title="Add">
              <Plus size={18} />
            </button>

            <button title="Attach files">
              <Paperclip size={18} />
            </button>

            <button title="Coding mode">
              <Sparkles size={17} />
              <span>Build</span>
            </button>

            <ModelPicker
              models={models}
              selected={selectedModel}
              onSelect={setSelectedModel}
              authenticated={true}
              onLockedPick={() => undefined}
            />
          </div>

          <button
            className="send-button"
            onClick={submit}
            disabled={!value.trim() || disabled}
            title="Send"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </div>

      <div className="composer-note">
        VEXION can make mistakes. Check important code before using it.
      </div>
    </div>
  );
}
