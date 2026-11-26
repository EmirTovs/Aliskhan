import type React from "react";
import { Search, Plus, X, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Material, type Page } from "../../../shared/api/client";
import PageTitle from "../../../components/ui/PageTitle";
function DataPage<T extends { id: string }>({
  kind,
  title,
  description,
  endpoint,
  columns,
  createLabel,
  createFields,
  createPath,
  query = "",
}: {
  kind: string;
  title: string;
  description: string;
  endpoint: string;
  columns: { label: string; render: (item: T) => React.ReactNode }[];
  createLabel?: string;
  createFields?: {
    name: string;
    label: string;
    type?: string;
    required?: boolean;
  }[];
  createPath?: string;
  query?: string;
}) {
  const [items, setItems] = useState<T[]>([]),
    [total, setTotal] = useState(0),
    [search, setSearch] = useState(""),
    [page, setPage] = useState(1),
    [busy, setBusy] = useState(true),
    [error, setError] = useState(""),
    [modal, setModal] = useState(false);
  const load = () => {
    setBusy(true);
    api<Page<T>>(
      `${endpoint}?page=${page}&page_size=20${search ? `&search=${encodeURIComponent(search)}` : ""}${query}`,
    )
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };
  useEffect(() => {
    load();
  }, [page, search, endpoint]);
  async function create(data: Record<string, string>) {
    try {
      await api(createPath || endpoint, {
        method: "POST",
        body: JSON.stringify(data),
      });
      setModal(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    }
  }
  return (
    <>
      <PageTitle
        eyebrow={kind.toUpperCase()}
        title={title}
        description={description}
        action={
          createLabel ? (
            <button className="primary-btn" onClick={() => setModal(true)}>
              <Plus size={17} />
              {createLabel}
            </button>
          ) : undefined
        }
      />
      {error && <div className="error-box">{error}</div>}
      <div className="panel data-panel">
        <div className="toolbar">
          <div className="search-box">
            <Search size={17} />
            <input
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              placeholder="Поиск по названию или коду…"
            />
          </div>
          <span className="result-count">
            Найдено: <b>{total}</b>
          </span>
          <button className="icon-button" onClick={load} title="Обновить">
            <RefreshCw size={17} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((c) => (
                  <th key={c.label}>{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  {columns.map((c) => (
                    <td key={c.label}>{c.render(item)}</td>
                  ))}
                </tr>
              ))}
              {!busy && !items.length && (
                <tr>
                  <td colSpan={columns.length} className="empty">
                    Ничего не найдено
                  </td>
                </tr>
              )}
              {busy && (
                <tr>
                  <td colSpan={columns.length} className="empty">
                    Загружаем данные…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="pagination">
          <span>
            Страница {page} · {total} записей
          </span>
          <div>
            <button
              className="secondary-btn small"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Назад
            </button>
            <button
              className="secondary-btn small"
              disabled={page * 20 >= total}
              onClick={() => setPage((p) => p + 1)}
            >
              Далее
            </button>
          </div>
        </div>
      </div>
      {modal && (
        <CreateModal
          title={createLabel || "Создать"}
          fields={createFields || []}
          onClose={() => setModal(false)}
          onSubmit={create}
        />
      )}
    </>
  );
}
function CreateModal({
  title,
  fields,
  onClose,
  onSubmit,
}: {
  title: string;
  fields: { name: string; label: string; type?: string; required?: boolean }[];
  onClose: () => void;
  onSubmit: (d: Record<string, string>) => void;
}) {
  const [data, setData] = useState<Record<string, string>>({});
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(data);
        }}
      >
        <div className="modal-head">
          <h3>{title}</h3>
          <button type="button" className="icon-button" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        {fields.map((f) => (
          <label key={f.name}>
            {f.label}
            <input
              type={f.type || "text"}
              required={f.required !== false}
              value={data[f.name] || ""}
              onChange={(e) => setData({ ...data, [f.name]: e.target.value })}
            />
          </label>
        ))}
        <div className="modal-actions">
          <button type="button" className="secondary-btn" onClick={onClose}>
            Отмена
          </button>
          <button className="primary-btn">Сохранить</button>
        </div>
      </form>
    </div>
  );
}
function Materials() {
  return (
    <DataPage<Material>
      kind="СПРАВОЧНИК СКЛАДА"
      title="Материалы"
      description="Сырьё и компоненты, используемые в производстве."
      endpoint="/materials"
      createLabel="Добавить материал"
      createFields={[
        { name: "code", label: "Код" },
        { name: "name", label: "Название" },
        { name: "unit", label: "Единица измерения" },
        { name: "description", label: "Описание", required: false },
      ]}
      columns={[
        { label: "КОД", render: (x) => <b className="strong">{x.code}</b> },
        { label: "НАИМЕНОВАНИЕ", render: (x) => x.name },
        {
          label: "ЕДИНИЦА",
          render: (x) => <span className="unit-pill">{x.unit}</span>,
        },
        {
          label: "ОПИСАНИЕ",
          render: (x) => <span className="muted">{x.description || "—"}</span>,
        },
        {
          label: "СОЗДАН",
          render: (x) => new Date(x.created_at).toLocaleDateString("ru-RU"),
        },
      ]}
    />
  );
}
export default Materials;
