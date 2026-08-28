import { useNavigate, useOutletContext } from "react-router-dom";
import type { BoardOutlet } from "../components/AppShell";
import MissionGrid from "../components/MissionGrid";
import { isForbiddenSeedCard } from "../lib/missions-api";

export default function Home() {
  const navigate = useNavigate();
  const { missions, selectedId, onFillCommand } = useOutletContext<BoardOutlet>();
  const rows = missions.filter((m) => !isForbiddenSeedCard(m));

  return (
    <MissionGrid
      missions={rows}
      selectedId={selectedId}
      onSelect={(id) => navigate(`/desk/m/${id}`)}
      onFillCommand={onFillCommand}
    />
  );
}
