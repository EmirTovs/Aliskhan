import { AlertTriangle } from "lucide-react";
function Stat({
  icon: Icon,
  label,
  value,
  note,
  warning,
}: {
  icon: any;
  label: string;
  value: string | number;
  note: string;
  warning?: boolean;
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span className="stat-icon">
          <Icon size={18} />
        </span>
        {warning && <span className="warning-mini">ВНИМАНИЕ</span>}
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-note">{note}</div>
    </div>
  );
}
export default Stat;
