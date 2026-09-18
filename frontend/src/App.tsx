import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

import Chat from "@/pages/Chat";
import Settings from "@/pages/Settings";
import Projects from "@/pages/Projects";
import Usage from "@/pages/Usage";
import Landing from "@/pages/Landing";
import Waitlist from "@/pages/Waitlist";
import Terms from "@/pages/Terms";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/waitlist" element={<Waitlist />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/usage" element={<Usage />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <Toaster
        position="top-right"
        richColors
        theme="light"
      />
    </>
  );
}
