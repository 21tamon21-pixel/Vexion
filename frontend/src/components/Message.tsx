type Props = {
  role: "user" | "assistant";
  content: string;
};

export default function Message({ role, content }: Props) {
  return (
    <div className={`message-row ${role}`}>
      <div className="message-content">
        {role === "assistant" && (
          <div className="assistant-name">
            <span className="assistant-dot">V</span>
            VEXION
          </div>
        )}

        <div className="message-text">
          {content}
        </div>
      </div>
    </div>
  );
}
