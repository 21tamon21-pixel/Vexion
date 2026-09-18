import { useEffect, useState } from "react";

export default function Preview() {
  const [project, setProject] = useState<{
    title?: string;
    html?: string;
  } | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("vexion-preview");

      if (saved) {
        setProject(JSON.parse(saved));
      }
    } catch {
      setProject(null);
    }
  }, []);

  return (
    <div className="preview-page">
      <header className="preview-header">
        <div className="preview-brand">
          <div className="brand-mark">V</div>
          <span>VEXION</span>
          <span className="preview-divider">/</span>
          <span className="preview-label">Preview</span>
        </div>
      </header>

      <main className="preview-main">
        {project?.html ? (
          <iframe
            title={project.title || "VEXION Preview"}
            className="preview-frame"
            sandbox="allow-scripts"
            srcDoc={project.html}
          />
        ) : (
          <div className="empty-preview">
            <div className="empty-preview-icon">V</div>
            <h1>No preview yet</h1>
            <p>
              Generated projects will appear here when VEXION creates them.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
