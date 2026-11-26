import type React from "react";
import {
  MessageCircle,
  Plus,
  ArrowUpRight,
  X,
  Flame,
  ChevronRight,
  CheckCircle2,
  Send,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, getToken, type User } from "../../../shared/api/client";
import PageTitle from "../../../components/ui/PageTitle";
function Assistant() {
  const [messages, setMessages] = useState<
    { role: string; content: string; status?: string; metadata?: any }[]
  >([]);
  const [value, setValue] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null),
    [conversations, setConversations] = useState<
      { id: string; title: string }[]
    >([]),
    [pendingProposal, setPendingProposal] = useState<any>(null);
  const controller = useState<AbortController | null>(null);
  const suggestions = [
    "Сколько материалов сейчас доступно на складе?",
    "Какие задания имеют дефицит?",
    "Рассчитай потребность для 500 свечей.",
    "Покажи историю поступлений соевого воска.",
  ];
  async function loadConversations() {
    try {
      const rows =
        await api<{ id: string; title: string }[]>("/ai/conversations");
      setConversations(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить диалоги");
    }
  }
  useEffect(() => {
    loadConversations();
  }, []);
  async function openConversation(id: string) {
    try {
      const rows = await api<any[]>(`/ai/conversations/${id}/messages`);
      setConversationId(id);
      setMessages(
        rows.map((x) => ({
          role: x.role,
          content: x.content,
          status: x.status,
          metadata: x.metadata,
        })),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки диалога");
    }
  }
  function newConversation() {
    setConversationId(null);
    setMessages([]);
    setPendingProposal(null);
    setError("");
  }
  async function confirmProposal() {
    if (!pendingProposal) return;
    if (
      !confirm(
        `Создать задание на ${pendingProposal.quantity} шт. по рецептуре «${pendingProposal.recipe}»? Система зарезервирует доступные материалы.`,
      )
    )
      return;
    try {
      const result = await api<any>("/ai/confirm-production-plan", {
        method: "POST",
        body: JSON.stringify({
          recipe_id: pendingProposal.recipe_id,
          planned_quantity: pendingProposal.quantity,
        }),
      });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Задание ${result.job_number} создано. Статус: ${result.status}. ${result.can_start ? "Материалов достаточно для запуска." : "Есть дефицит материалов — запуск заблокирован."}`,
        },
      ]);
      setPendingProposal(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать задание");
    }
  }
  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = value.trim();
    if (!text || busy) return;
    setError("");
    setValue("");
    setMessages((m) => [
      ...m,
      { role: "user", content: text },
      { role: "assistant", content: "Анализирую данные…", status: "pending" },
    ]);
    setBusy(true);
    const aborter = new AbortController();
    controller[1](aborter);
    try {
      const token = getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1"}/ai/chat/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            message: text,
            conversation_id: conversationId,
          }),
          signal: aborter.signal,
        },
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const reader = response.body?.getReader();
      if (!reader) throw new Error("Поток ответа недоступен");
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";
        for (const chunk of chunks) {
          const line = chunk.split("\n").find((x) => x.startsWith("data: "));
          if (!line) continue;
          const event = JSON.parse(line.slice(6));
          if (event.type === "error") throw new Error(event.message);
          if (event.type === "done") {
            setConversationId(event.conversation_id);
            setMessages((m) => [
              ...m.slice(0, -1),
              {
                role: "assistant",
                content: event.message,
                metadata: {
                  model: event.model,
                  tools: event.tools,
                  proposal: event.proposal,
                },
              },
            ]);
            if (event.proposal) setPendingProposal(event.proposal);
          }
        }
      }
      loadConversations();
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setMessages((m) =>
          m.map((x) =>
            x.status === "pending"
              ? { ...x, content: "Ответ прерван.", status: "interrupted" }
              : x,
          ),
        );
      } else {
        const msg = err instanceof Error ? err.message : "Ошибка AI";
        setError(msg);
        setMessages((m) =>
          m.map((x) =>
            x.status === "pending"
              ? {
                  ...x,
                  content: `Не удалось получить ответ: ${msg}`,
                  status: "error",
                }
              : x,
          ),
        );
      }
    } finally {
      setBusy(false);
      controller[1](null);
    }
  }
  function stop() {
    controller[0]?.abort();
  }
  return (
    <>
      <PageTitle
        eyebrow="CANDLEFLOW INTELLIGENCE"
        title="AI-ассистент"
        description="Помощник по складу, рецептурам, себестоимости и производственному планированию."
        action={
          <button className="secondary-btn" onClick={newConversation}>
            <Plus size={16} /> Новый диалог
          </button>
        }
      />
      {error && <div className="error-box">{error}</div>}
      <div className="assistant-layout">
        <div className="assistant-main panel">
          <div className="assistant-header">
            <div className="assistant-avatar">
              <MessageCircle />
            </div>
            <div>
              <b>CandleFlow Assistant</b>
              <small>
                <span className="status-pulse" /> Подключение к производственным
                данным
              </small>
            </div>
            <span className="model-tag">RESPONSES API</span>
          </div>
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-message assistant">
                <div className="chat-avatar">
                  <Flame size={15} />
                </div>
                <div className="chat-bubble">
                  Здравствуйте! Я CandleFlow AI. Могу анализировать складские
                  остатки, дефициты, партии и себестоимость, а также подготовить
                  предварительный план производства. Любое создание задания
                  потребует отдельного подтверждения.
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div className={`chat-message ${m.role}`} key={i}>
                <div className="chat-avatar">
                  {m.role === "assistant" ? (
                    <Flame size={15} />
                  ) : (
                    <span>Вы</span>
                  )}
                </div>
                <div className="chat-bubble" style={{ whiteSpace: "pre-wrap" }}>
                  {m.content}
                  {m.metadata?.proposal && (
                    <div
                      style={{
                        marginTop: 10,
                        padding: 10,
                        border: "1px solid #dfe6d8",
                        borderRadius: 8,
                        background: "#fff",
                      }}
                    >
                      <b style={{ display: "block", marginBottom: 6 }}>
                        Предварительный план · {m.metadata.proposal.recipe}
                      </b>
                      <span>
                        {m.metadata.proposal.quantity} шт. ·{" "}
                        {m.metadata.proposal.can_start
                          ? "Материалов достаточно"
                          : "Есть дефицит"}
                      </span>
                      <button
                        type="button"
                        className="primary-btn"
                        style={{ display: "block", marginTop: 10 }}
                        onClick={() => setPendingProposal(m.metadata.proposal)}
                      >
                        Подтвердить создание задания
                      </button>
                    </div>
                  )}
                  {m.metadata?.model && (
                    <small
                      style={{ display: "block", opacity: 0.65, marginTop: 8 }}
                    >
                      Модель: {m.metadata.model}
                      {m.metadata.tools?.length
                        ? ` · Инструменты: ${m.metadata.tools.join(", ")}`
                        : ""}
                    </small>
                  )}
                </div>
              </div>
            ))}
          </div>
          <form className="chat-input" onSubmit={send}>
            <input
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Спросите о запасах или производстве…"
              disabled={busy}
            />
            {busy ? (
              <button type="button" className="danger-btn" onClick={stop}>
                Стоп
              </button>
            ) : (
              <button className="primary-btn" disabled={!value.trim()}>
                <Send size={17} />
              </button>
            )}
          </form>
          {pendingProposal && (
            <div className="warning-box">
              План подготовлен.{" "}
              <button
                type="button"
                className="primary-btn"
                onClick={confirmProposal}
              >
                Подтвердить и создать задание
              </button>
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setPendingProposal(null)}
              >
                Отмена
              </button>
            </div>
          )}
          <div className="chat-disclaimer">
            AI использует данные системы. Перед выполнением производственных
            действий требуется подтверждение.
          </div>
        </div>
        <div className="assistant-side panel">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span className="eyebrow">ИСТОРИЯ ДИАЛОГОВ</span>
            <button className="text-btn" onClick={loadConversations}>
              Обновить
            </button>
          </div>
          {conversations.slice(0, 8).map((c) => (
            <button
              className="prompt-chip"
              key={c.id}
              onClick={() => openConversation(c.id)}
            >
              {c.title}
              <ChevronRight size={14} />
            </button>
          ))}
          {conversations.length === 0 && (
            <p className="muted small-note">Сохранённых диалогов пока нет.</p>
          )}
          <div className="form-divider">ПРИМЕРЫ ЗАПРОСОВ</div>
          {suggestions.map((x) => (
            <button className="prompt-chip" key={x} onClick={() => setValue(x)}>
              {x}
              <ArrowUpRight size={14} />
            </button>
          ))}
          <div className="assistant-note">
            <CheckCircle2 size={17} />
            <div>
              <b>Безопасные операции</b>
              <p>
                Ассистент сначала показывает расчёт. Создание производственного
                задания выполняется только после вашего подтверждения.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
export default Assistant;
