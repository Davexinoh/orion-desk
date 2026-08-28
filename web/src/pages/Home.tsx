import { useNavigate, useOutletContext } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import MissionGrid from "../components/MissionGrid";

export default function Home() {
  const navigate = useNavigate();
  const { missions, selectedId, onFillCommand } = useOutletContext<BoardOutlet>();

  return (
    <MissionGrid
      missions={missions}
      selectedId={selectedId}
      onSelect={(id) => navigate(`/desk/m/${id}`)}
      onFillCommand={onFillCommand}
    />
  );
}
