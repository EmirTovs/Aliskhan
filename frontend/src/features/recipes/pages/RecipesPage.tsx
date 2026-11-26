import type React from "react";
import { Plus, X, Flame } from "lucide-react";
import { useEffect, useState } from "react";
import Status from "../../../components/ui/StatusBadge";
import {
  api,
  fmt,
  type Recipe,
  type Material,
  type Page,
} from "../../../shared/api/client";
import PageTitle from "../../../components/ui/PageTitle";
function Recipes() {
  const [items, setItems] = useState<Recipe[]>([]),
    [materials, setMaterials] = useState<Material[]>([]),
    [error, setError] = useState(""),
    [modal, setModal] = useState(false);
  const load = () =>
    Promise.all([
      api<{ items: Recipe[]; total: number }>("/recipes?limit=100&offset=0"),
      api<Page<Material>>("/materials?page=1&page_size=100"),
    ])
      .then(([r, m]) => {
        setItems(r.items);
        setMaterials(m.items);
      })
      .catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);
  return (
    <>
      <PageTitle
        eyebrow="ТЕХНОЛОГИЧЕСКИЕ КАРТЫ"
        title="Рецептуры"
        description="Состав продукции и нормы расхода материалов на единицу."
        action={
          <button className="primary-btn" onClick={() => setModal(true)}>
            <Plus size={17} /> Новая рецептура
          </button>
        }
      />
      {error && <div className="error-box">{error}</div>}
      <div className="recipe-grid">
        {items.map((r) => (
          <div className="panel recipe-card" key={r.id}>
            <div className="recipe-top">
              <span className="recipe-icon">
                <Flame />
              </span>
              <Status value={r.is_active ? "accepted" : "rejected"} />
            </div>
            <div className="recipe-code">{r.code}</div>
            <h3>{r.name}</h3>
            <p>{r.description || "Технологическая карта производства"}</p>
            <div className="recipe-items">
              <b>СОСТАВ РЕЦЕПТУРЫ</b>
              {r.items.map((i) => (
                <div key={i.id}>
                  <span>
                    {materials.find((m) => m.id === i.material_id)?.name ||
                      i.material_id.slice(0, 8)}
                  </span>
                  <strong>
                    {fmt(i.quantity_per_unit, 4)}{" "}
                    {materials.find((m) => m.id === i.material_id)?.unit ||
                      "кг"}
                  </strong>
                </div>
              ))}
            </div>
          </div>
        ))}
        {!items.length && (
          <div className="panel empty-card">Рецептуры пока не созданы</div>
        )}
      </div>
      {modal && (
        <RecipeModal
          materials={materials}
          onClose={() => setModal(false)}
          onSaved={() => {
            setModal(false);
            load();
          }}
        />
      )}
    </>
  );
}
function RecipeModal({
  materials,
  onClose,
  onSaved,
}: {
  materials: Material[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [code, setCode] = useState(""),
    [name, setName] = useState(""),
    [description, setDescription] = useState(""),
    [material, setMaterial] = useState(materials[0]?.id || ""),
    [norm, setNorm] = useState(""),
    [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/recipes", {
        method: "POST",
        body: JSON.stringify({
          code,
          name,
          description: description || null,
          items: [{ material_id: material, quantity_per_unit: norm }],
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
          <h3>Новая рецептура</h3>
          <button type="button" className="icon-button" onClick={onClose}>
            <X />
          </button>
        </div>
        <label>
          Код рецептуры
          <input
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        </label>
        <label>
          Название
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          Описание
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <div className="form-divider">НОРМА РАСХОДА</div>
        <label>
          Материал
          <select
            value={material}
            onChange={(e) => setMaterial(e.target.value)}
          >
            {materials.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Количество на одну единицу
          <input
            type="number"
            min="0.000001"
            step="0.000001"
            required
            value={norm}
            onChange={(e) => setNorm(e.target.value)}
          />
        </label>
        {error && <div className="error-box">{error}</div>}
        <div className="modal-actions">
          <button type="button" className="secondary-btn" onClick={onClose}>
            Отмена
          </button>
          <button className="primary-btn">Сохранить рецепт</button>
        </div>
      </form>
    </div>
  );
}
export default Recipes;
