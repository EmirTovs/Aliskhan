const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
export type User = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
};
export type Page<T> = {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};
export type Material = {
  id: string;
  code: string;
  name: string;
  unit: string;
  description?: string | null;
  created_at: string;
};
export type Supplier = {
  id: string;
  name: string;
  contact_name?: string | null;
  phone?: string | null;
  email?: string | null;
  notes?: string | null;
  created_at: string;
};
export type Batch = {
  id: string;
  batch_number: string;
  material_id: string;
  supplier_id: string;
  quantity: string;
  reserved_quantity: string;
  purchase_price: string;
  currency: string;
  cost_rub: string;
  received_at: string;
  status: string;
  created_at: string;
};
export type Recipe = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  items: { id: string; material_id: string; quantity_per_unit: string }[];
};
export type Job = {
  id: string;
  job_number: string;
  recipe_id: string;
  planned_quantity: string;
  status: string;
  created_by: string;
  created_at: string;
  planned_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  items?: {
    material_id: string;
    material_name: string;
    unit: string;
    required_quantity: string;
    reserved_quantity: string;
    consumed_quantity: string;
    deficit_quantity: string;
    is_available: boolean;
  }[];
  can_start?: boolean;
};
export function setToken(token: string | null) {
  if (token) localStorage.setItem("cf_token", token);
  else localStorage.removeItem("cf_token");
}
export function getToken() {
  return localStorage.getItem("cf_token");
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;
  const body = await response
    .json()
    .catch(() => ({ detail: `HTTP ${response.status}` }));
  if (!response.ok)
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail || body),
    );
  return body as T;
}
export const fmt = (v: string | number | undefined, digits = 2) =>
  Number(v || 0).toLocaleString("ru-RU", { maximumFractionDigits: digits });
