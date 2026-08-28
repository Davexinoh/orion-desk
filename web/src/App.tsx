import { Navigate, Route, Routes } from "react-router-dom";
import DeskGate from "./components/DeskGate";
import { AuthProvider } from "./lib/AuthContext";
import { DeskProvider } from "./lib/store";
import Approvals from "./pages/Approvals";
import Home from "./pages/Home";
import Landing from "./pages/Landing";
import Memory from "./pages/Memory";
import MissionRun from "./pages/MissionRun";
import Receipts from "./pages/Receipts";
import Settings from "./pages/Settings";
import SignIn from "./pages/SignIn";
import TelegramPreview from "./pages/TelegramPreview";

export default function App() {
  return (
    <AuthProvider>
    <DeskProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/sign-in" element={<SignIn />} />
        <Route path="/desk" element={<DeskGate />}>
          <Route index element={<Home />} />
          <Route path="m/:id" element={<MissionRun />} />
          <Route path="approvals" element={<Approvals />} />
          <Route path="receipts" element={<Receipts />} />
          <Route path="memory" element={<Memory />} />
          <Route path="settings" element={<Settings />} />
          <Route path="telegram" element={<TelegramPreview />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DeskProvider>
    </AuthProvider>
  );
}
