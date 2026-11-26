import {
  LayoutDashboard,
  Boxes,
  Package,
  Factory,
  BookOpen,
  Truck,
  MessageCircle,
} from "lucide-react";
import type { Tab } from "../shared/types/navigation";
export const navigation: { id: Tab; label: string; icon: any }[] = [
  { id: "overview", label: "Обзор", icon: LayoutDashboard },
  { id: "materials", label: "Материалы", icon: Boxes },
  { id: "batches", label: "Партии", icon: Package },
  { id: "production", label: "Производство", icon: Factory },
  { id: "recipes", label: "Рецептуры", icon: BookOpen },
  { id: "suppliers", label: "Поставщики", icon: Truck },
  { id: "assistant", label: "AI-ассистент", icon: MessageCircle },
];
export function roleName(role: string) {
  return (
    (
      {
        warehouse: "Склад",
        technologist: "Технолог",
        manager: "Менеджер",
      } as Record<string, string>
    )[role] || role
  );
}
