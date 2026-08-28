export default function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <h1 className="od-placeholder-title">{title}</h1>
      <p className="od-placeholder-body">Not built yet.</p>
    </div>
  );
}
