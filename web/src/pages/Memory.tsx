import { FormEvent, useState } from "react";
import { memory as seed, type MemoryFact, type MemoryGroup } from "../lib/demo-data";

function nextId(prefix: string) {
  return `${prefix}-${Date.now()}`;
}

function FactList({
  facts,
  onRemove,
  onAdd,
}: {
  facts: MemoryFact[];
  onRemove: (id: string) => void;
  onAdd: (text: string) => void;
}) {
  const [draft, setDraft] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    onAdd(text);
    setDraft("");
  }

  return (
    <div>
      <ul className="od-fact-list">
        {facts.map((f) => (
          <li key={f.id}>
            <span>{f.text}</span>
            <button type="button" className="od-fact-x" onClick={() => onRemove(f.id)} aria-label="Remove">
              Remove
            </button>
          </li>
        ))}
      </ul>
      <form className="od-fact-add" onSubmit={submit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a fact"
          aria-label="Add a fact"
        />
        <button type="submit" className="od-btn od-btn-ghost">
          Add
        </button>
      </form>
    </div>
  );
}

export default function Memory() {
  const [user, setUser] = useState<MemoryFact[]>(seed.user);
  const [project, setProject] = useState<MemoryGroup[]>(seed.project);
  const [execution, setExecution] = useState<MemoryFact[]>(seed.execution);

  return (
    <div className="od-memory">
      <h1 className="od-page-title">Memory</h1>

      <section className="od-memory-section">
        <h2>User memory</h2>
        <FactList
          facts={user}
          onRemove={(id) => setUser((p) => p.filter((f) => f.id !== id))}
          onAdd={(text) => setUser((p) => [...p, { id: nextId("u"), text }])}
        />
      </section>

      <section className="od-memory-section">
        <h2>Project memory</h2>
        {project.map((g) => (
          <div key={g.id} className="od-memory-group">
            <h3>{g.title}</h3>
            <FactList
              facts={g.facts}
              onRemove={(id) =>
                setProject((prev) =>
                  prev.map((pg) =>
                    pg.id === g.id ? { ...pg, facts: pg.facts.filter((f) => f.id !== id) } : pg
                  )
                )
              }
              onAdd={(text) =>
                setProject((prev) =>
                  prev.map((pg) =>
                    pg.id === g.id
                      ? { ...pg, facts: [...pg.facts, { id: nextId(g.id), text }] }
                      : pg
                  )
                )
              }
            />
          </div>
        ))}
      </section>

      <section className="od-memory-section">
        <h2>Execution memory</h2>
        <FactList
          facts={execution}
          onRemove={(id) => setExecution((p) => p.filter((f) => f.id !== id))}
          onAdd={(text) => setExecution((p) => [...p, { id: nextId("e"), text }])}
        />
      </section>
    </div>
  );
}
