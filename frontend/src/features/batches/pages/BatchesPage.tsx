import type React from "react";
import {
  LayoutDashboard,
  Boxes,
  Package,
  Factory,
  BookOpen,
  Truck,
  MessageCircle,
  LogOut,
  Search,
  Bell,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  Menu,
  X,
  Flame,
  ChevronRight,
  ChevronLeft,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock3,
  Send,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  api,
  fmt,
  type Material,
  type Supplier,
  type Batch,
  type Page,
} from "../../../shared/api/client";
import PageTitle from "../../../components/ui/PageTitle";
import Status from "../../../components/ui/StatusBadge";
function Batches() {
  const [items, setItems] = useState<Batch[]>([]),
    [materials, setMaterials] = useState<Material[]>([]),
    [suppliers, setSuppliers] = useState<Supplier[]>([]),
    [status, setStatus] = useState(""),
    [busy, setBusy] = useState(true),
    [error, setError] = useState(""),
    [receipt, setReceipt] = useState(false);
  const load = () => {
    setBusy(true);
    Promise.all([
      api<Page<Batch>>(
        `/batches?page=1&page_size=100${status ? `&status=${status}` : ""}&sort_by=received_at&sort_order=desc`,
      ),
      api<Page<Material>>("/materials?page=1&page_size=100"),
      api<Page<Supplier>>("/suppliers?page=1&page_size=100"),
    ])
      .then(([b, m, s]) => {
        setItems(b.items);
        setMaterials(m.items);
        setSuppliers(s.items);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(false));
  };
  useEffect(load, [status]);
  async function change(b: Batch, s: string) {
    try {
      await api(`/batches/${b.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: s }),
      });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="СКЛАДСКИЕ ОПЕРАЦИИ"
        title="Партии материалов"
        description="Поступления, контроль качества и доступность сырья."
        action={
          <button className="primary-btn" onClick={() => setReceipt(true)}>
            <Plus size={17} /> Новое поступление
          </button>
        }
      />
      {error && <div className="error-box">{error}</div>}
      <div className="panel data-panel">
        <div className="toolbar">
          <div className="filter-tabs">
            <button
              className={!status ? "selected" : ""}
              onClick={() => setStatus("")}
            >
              Все партии
            </button>
            <button
              className={status === "pending" ? "selected" : ""}
              onClick={() => setStatus("pending")}
            >
              Ожидают
            </button>
            <button
              className={status === "accepted" ? "selected" : ""}
              onClick={() => setStatus("accepted")}
            >
              Принятые
            </button>
            <button
              className={status === "rejected" ? "selected" : ""}
              onClick={() => setStatus("rejected")}
            >
              Отклонённые
            </button>
          </div>
          <button className="icon-button" onClick={load}>
            <RefreshCw size={17} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>НОМЕР ПАРТИИ</th>
                <th>МАТЕРИАЛ</th>
                <th>ПОСТУПИЛА</th>
                <th>ОБЪЁМ</th>
                <th>РЕЗЕРВ</th>
                <th>СВОБОДНО</th>
                <th>СТАТУС / ДЕЙСТВИЕ</th>
              </tr>
            </thead>
            <tbody>
              {items.map((b) => {
                const m = materials.find((x) => x.id === b.material_id);
                return (
                  <tr key={b.id}>
                    <td className="strong">{b.batch_number}</td>
                    <td>{m?.name || b.material_id.slice(0, 8)}</td>
                    <td>
                      {new Date(b.received_at).toLocaleDateString("ru-RU")}
                    </td>
                    <td>
                      {fmt(b.quantity)} {m?.unit || "кг"}
                    </td>
                    <td>{fmt(b.reserved_quantity)}</td>
                    <td className="strong">
                      {fmt(Number(b.quantity) - Number(b.reserved_quantity))}
                    </td>
                    <td>
                      <div className="inline-status">
                        <Status value={b.status} />
                        {b.status === "pending" && (
                          <>
                            <button
                              className="mini-action accept"
                              onClick={() => change(b, "accepted")}
                              title="Принять"
                            >
                              <CheckCircle2 size={15} />
                            </button>
                            <button
                              className="mini-action reject"
                              onClick={() => change(b, "rejected")}
                              title="Отклонить"
                            >
                              <X size={15} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {!busy && !items.length && (
                <tr>
                  <td colSpan={7} className="empty">
                    Партии не найдены
                  </td>
                </tr>
              )}
              {busy && (
                <tr>
                  <td colSpan={7} className="empty">
                    Загружаем…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      {receipt && (
        <ReceiptModal
          materials={materials}
          suppliers={suppliers}
          onClose={() => setReceipt(false)}
          onSaved={() => {
            setReceipt(false);
            load();
          }}
        />
      )}
    </>
  );
}
function ReceiptModal({
  materials,
  suppliers,
  onClose,
  onSaved,
}: {
  materials: Material[];
  suppliers: Supplier[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [supplier, setSupplier] = useState(suppliers[0]?.id || ""),
    [date, setDate] = useState(new Date().toISOString().slice(0, 10)),
    [material, setMaterial] = useState(materials[0]?.id || ""),
    [quantity, setQuantity] = useState(""),
    [price, setPrice] = useState(""),
    [currency, setCurrency] = useState("RUB"),
    [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/batches/receipts", {
        method: "POST",
        body: JSON.stringify({
          supplier_id: supplier,
          received_at: date,
          items: [
            {
              material_id: material,
              quantity,
              purchase_price: price,
              currency,
            },
          ],
        }),
      });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
      >
        <div className="modal-head">
          <h3>Новое поступление</h3>
          <button type="button" className="icon-button" onClick={onClose}>
            <X />
          </button>
        </div>
        <label>
          Поставщик
          <select
            required
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
          >
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Дата поступления
          <input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <div className="form-divider">ПОЗИЦИЯ ПОСТАВКИ</div>
        <label>
          Материал
          <select
            required
            value={material}
            onChange={(e) => setMaterial(e.target.value)}
          >
            {materials.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.unit})
              </option>
            ))}
          </select>
        </label>
        <div className="form-row">
          <label>
            Количество
            <input
              type="number"
              min="0.000001"
              step="0.000001"
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </label>
          <label>
            Цена за единицу
            <input
              type="number"
              min="0.000001"
              step="0.000001"
              required
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </label>
        </div>
        <label>
          Валюта
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
          >
            <option>RUB</option>
            <option>USD</option>
            <option>EUR</option>
          </select>
        </label>
        {error && <div className="error-box">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-btn" onClick={onClose}>
            Отмена
          </button>
          <button className="primary-btn">Создать партию</button>
        </div>
      </form>
    </div>
  );
}
export default Batches;
