interface TechCardProps {
  title: string;
  badge: string;
}

export default function TechCard({ title, badge }: TechCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">{title}</h2>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs text-emerald-700">
          {badge}
        </span>
      </div>
    </article>
  );
}
