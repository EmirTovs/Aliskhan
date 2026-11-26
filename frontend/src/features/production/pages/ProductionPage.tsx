import type React from "react";
import { Plus, X, ChevronRight, RefreshCw, AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import { api, fmt, type Recipe, type Job } from "../../../shared/api/client";
import PageTitle from "../../../components/ui/PageTitle";
import Status from "../../../components/ui/StatusBadge";
function Production() {
  const [jobs, setJobs] = useState<Job[]>([]),
    [recipes, setRecipes] = useState<Recipe[]>([]),
    [selected, setSelected] = useState<Job | null>(null),
    [modal, setModal] = useState(false),
    [recipe, setRecipe] = useState(""),
    [quantity, setQuantity] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(true);
  const load = () => {
    setBusy(true);
    Promise.all([
      api<{ items: Job[]; total: number }>(
        "/production-jobs?limit=100&offset=0",
      ),
      api<{ items: Recipe[]; total: number }>("/recipes?limit=100&offset=0"),
    ])
      .then(([j, r]) => {
        setJobs(j.items);
        setRecipes(r.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };
  useEffect(() => {
    load();
  }, []);
  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      const j = await api<Job>("/production-jobs", {
        method: "POST",
        body: JSON.stringify({ recipe_id: recipe, planned_quantity: quantity }),
      });
      setModal(false);
      setSelected(j);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  async function action(job: Job, act: string) {
    if (
      !confirm(
        `Подтвердить действие: ${act === "start" ? "запуск" : act === "cancel" ? "отмена" : "завершение"} задания ${job.job_number}?`,
      )
    )
      return;
    try {
      const updated = await api<Job>(`/production-jobs/${job.id}/${act}`, {
        method: "POST",
      });
      setSelected(updated);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  async function details(j: Job) {
    try {
      setSelected(await api<Job>(`/production-jobs/${j.id}`));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ПЛАНИРОВАНИЕ ВЫПУСКА"
        title="Производство"
        description="Производственные задания, резервирование сырья и контроль выпуска."
        action={
          <button className="primary-btn" onClick={() => setModal(true)}>
            <Plus size={17} /> Создать задание
          </button>
        }
      />
      {error && <div className="error-box">{error}</div>}
      <div className="panel data-panel">
        <div className="panel-head padded">
          <div>
            <h3>Производственные задания</h3>
            <p>Всего: {jobs.length}</p>
          </div>
          <button className="icon-button" onClick={load}>
            <RefreshCw size={17} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>НОМЕР</th>
                <th>РЕЦЕПТУРА</th>
                <th>ПЛАН, ШТ.</th>
                <th>СТАТУС</th>
                <th>СОЗДАНО</th>
                <th>ДЕЙСТВИЯ</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td className="strong">{j.job_number}</td>
                  <td>
                    {recipes.find((r) => r.id === j.recipe_id)?.name ||
                      j.recipe_id.slice(0, 8)}
                  </td>
                  <td>{fmt(j.planned_quantity, 0)}</td>
                  <td>
                    <Status value={j.status} />
                  </td>
                  <td>{new Date(j.created_at).toLocaleDateString("ru-RU")}</td>
                  <td>
                    <button className="text-btn" onClick={() => details(j)}>
                      Открыть <ChevronRight size={15} />
                    </button>
                  </td>
                </tr>
              ))}
              {!busy && !jobs.length && (
                <tr>
                  <td colSpan={6} className="empty">
                    Заданий пока нет
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <div
            className="modal wide-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <span className="eyebrow">КАРТОЧКА ПРОИЗВОДСТВА</span>
                <h3>{selected.job_number}</h3>
              </div>
              <button className="icon-button" onClick={() => setSelected(null)}>
                <X />
              </button>
            </div>
            <div className="job-meta">
              <div>
                <small>План выпуска</small>
                <b>{fmt(selected.planned_quantity, 0)} шт.</b>
              </div>
              <div>
                <small>Статус</small>
                <Status value={selected.status} />
              </div>
              <div>
                <small>Можно запускать</small>
                <b>{selected.can_start ? "Да" : "Нет"}</b>
              </div>
            </div>
            <div className="form-divider">ПОТРЕБНОСТЬ В МАТЕРИАЛАХ</div>
            {(selected.items || []).map((i) => (
              <div className="job-material" key={i.material_id}>
                <div>
                  <b>{i.material_name}</b>
                  <small>
                    Требуется {fmt(i.required_quantity, 3)} {i.unit}
                  </small>
                </div>
                <div className="job-amounts">
                  <span>Резерв: {fmt(i.reserved_quantity, 3)}</span>
                  <span
                    className={Number(i.deficit_quantity) > 0 ? "text-red" : ""}
                  >
                    Дефицит: {fmt(i.deficit_quantity, 3)}
                  </span>
                </div>
              </div>
            ))}
            {selected.items?.some((i) => Number(i.deficit_quantity) > 0) && (
              <div className="warning-box">
                <AlertTriangle size={17} /> Недостаточно материалов. Запуск
                задания заблокирован.
              </div>
            )}
            <div className="modal-actions">
              {selected.status === "draft" && (
                <button
                  className="danger-btn"
                  onClick={() => action(selected, "cancel")}
                >
                  Отменить
                </button>
              )}
              {selected.status === "draft" && (
                <button
                  className="primary-btn"
                  disabled={!selected.can_start}
                  onClick={() => action(selected, "start")}
                >
                  Запустить производство
                </button>
              )}
              {selected.status === "in_progress" && (
                <button
                  className="primary-btn"
                  onClick={() => action(selected, "complete")}
                >
                  Завершить производство
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(false)}>
          <form
            className="modal"
            onClick={(e) => e.stopPropagation()}
            onSubmit={create}
          >
            <div className="modal-head">
              <h3>Новое производственное задание</h3>
              <button
                type="button"
                className="icon-button"
                onClick={() => setModal(false)}
              >
                <X />
              </button>
            </div>
            <label>
              Рецептура
              <select
                required
                value={recipe}
                onChange={(e) => setRecipe(e.target.value)}
              >
                <option value="">Выберите рецептуру</option>
                {recipes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Планируемое количество, шт.
              <input
                type="number"
                min="0.000001"
                step="1"
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </label>
            <div className="muted small-note">
              При создании задания система автоматически зарезервирует доступные
              материалы по FIFO.
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setModal(false)}
              >
                Отмена
              </button>
              <button className="primary-btn">
                Создать и рассчитать резерв
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
export default Production;
