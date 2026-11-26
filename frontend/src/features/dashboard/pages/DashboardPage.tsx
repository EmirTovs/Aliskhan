import {
  Boxes,
  Package,
  Factory,
  BookOpen,
  ArrowUpRight,
  ChevronRight,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  api,
  fmt,
  type Material,
  type Batch,
  type Job,
  type Page,
} from "../../../shared/api/client";
import type { Tab } from "../../../shared/types/navigation";
import PageTitle from "../../../components/ui/PageTitle";
import Stat from "../../../components/ui/StatCard";
import Status from "../../../components/ui/StatusBadge";
function Overview({ onNavigate }: { onNavigate: (t: Tab) => void }) {
  const [materials, setMaterials] = useState<Material[]>([]),
    [batches, setBatches] = useState<Batch[]>([]),
    [jobs, setJobs] = useState<Job[]>([]),
    [busy, setBusy] = useState(true),
    [err, setErr] = useState("");
  const load = () => {
    setBusy(true);
    Promise.all([
      api<Page<Material>>("/materials?page=1&page_size=100"),
      api<Page<Batch>>(
        "/batches?page=1&page_size=100&sort_by=received_at&sort_order=desc",
      ),
      api<{ items: Job[]; total: number }>(
        "/production-jobs?limit=100&offset=0",
      ),
    ])
      .then(([m, b, j]) => {
        setMaterials(m.items);
        setBatches(b.items);
        setJobs(j.items);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };
  useEffect(load, []);
  const free = batches
      .filter((b) => b.status === "accepted")
      .reduce(
        (s, b) => s + Number(b.quantity) - Number(b.reserved_quantity),
        0,
      ),
    deficits = jobs.filter((j) =>
      j.items?.some((i) => Number(i.deficit_quantity) > 0),
    ).length;
  return (
    <>
      <PageTitle
        eyebrow="ПАНЕЛЬ УПРАВЛЕНИЯ"
        title="Добро пожаловать в CandleFlow"
        description="Сводка производства, склада и текущих задач."
        action={
          <button className="secondary-btn" onClick={load}>
            <RefreshCw size={16} /> Обновить
          </button>
        }
      />
      {err && <div className="error-box">{err}</div>}
      <div className="welcome-banner">
        <div>
          <span className="banner-tag">
            <span /> ПРОИЗВОДСТВО ПОД КОНТРОЛЕМ
          </span>
          <h2>
            Каждая свеча начинается
            <br />с точного расчёта.
          </h2>
          <p>
            Следите за запасами, планируйте выпуск и держите процессы в балансе.
          </p>
          <button
            className="banner-btn"
            onClick={() => onNavigate("production")}
          >
            Перейти к производству <ArrowUpRight size={16} />
          </button>
        </div>
        <div className="banner-art">
          <div className="glow" />
          <div className="candle candle-a">
            <i />
          </div>
          <div className="candle candle-b">
            <i />
          </div>
          <div className="candle candle-c">
            <i />
          </div>
        </div>
      </div>
      <div className="section-heading">
        <div>
          <h3>Показатели системы</h3>
          <p>Актуальные данные из вашего склада</p>
        </div>
        <span className="live-label">
          <i /> LIVE DATA
        </span>
      </div>
      <div className="stats-grid">
        <Stat
          icon={Boxes}
          label="Материалы"
          value={busy ? "—" : materials.length}
          note="Позиций в справочнике"
        />
        <Stat
          icon={Package}
          label="Доступный запас"
          value={busy ? "—" : `${fmt(free)} кг`}
          note="Принятые партии за вычетом резерва"
        />
        <Stat
          icon={Factory}
          label="Задания производства"
          value={busy ? "—" : jobs.length}
          note="Всего создано заданий"
        />
        <Stat
          icon={AlertTriangle}
          label="Дефицит материалов"
          value={busy ? "—" : deficits}
          note="Заданий с нехваткой сырья"
          warning={deficits > 0}
        />
      </div>
      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Последние партии</h3>
              <p>Недавно поступившее сырьё</p>
            </div>
            <button className="text-btn" onClick={() => onNavigate("batches")}>
              Все партии <ArrowUpRight size={15} />
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ПАРТИЯ</th>
                  <th>МАТЕРИАЛ ID</th>
                  <th>КОЛИЧЕСТВО</th>
                  <th>СТАТУС</th>
                </tr>
              </thead>
              <tbody>
                {batches.slice(0, 5).map((b) => (
                  <tr key={b.id}>
                    <td className="strong">{b.batch_number}</td>
                    <td className="mono">{b.material_id.slice(0, 8)}…</td>
                    <td>{fmt(b.quantity)} кг</td>
                    <td>
                      <Status value={b.status} />
                    </td>
                  </tr>
                ))}
                {!busy && !batches.length && (
                  <tr>
                    <td colSpan={4} className="empty">
                      Партии пока не поступали
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        <div className="panel quick-panel">
          <div className="panel-head">
            <div>
              <h3>Быстрые действия</h3>
              <p>Перейти к основным процессам</p>
            </div>
          </div>
          {[
            {
              icon: Package,
              title: "Принять поставку",
              desc: "Зарегистрировать новую партию",
              tab: "batches" as Tab,
            },
            {
              icon: Factory,
              title: "Создать задание",
              desc: "Запланировать выпуск продукции",
              tab: "production" as Tab,
            },
            {
              icon: BookOpen,
              title: "Открыть рецептуры",
              desc: "Нормы расхода сырья",
              tab: "recipes" as Tab,
            },
          ].map((x) => (
            <button
              className="quick-action"
              key={x.title}
              onClick={() => onNavigate(x.tab)}
            >
              <span className="quick-icon">
                <x.icon size={18} />
              </span>
              <span>
                <b>{x.title}</b>
                <small>{x.desc}</small>
              </span>
              <ChevronRight size={17} />
            </button>
          ))}
        </div>
      </div>
      <div className="footer-note">
        CandleFlow AI <span>·</span> Данные обновляются из производственной
        системы
      </div>
    </>
  );
}
export default Overview;
