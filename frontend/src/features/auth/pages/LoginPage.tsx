import type React from "react";
import { useState } from "react";
import { api, setToken, type User } from "../../../shared/api/client";
import { Flame, ArrowUpRight } from "lucide-react";
function Login({
  onLogin,
  onError,
  error,
}: {
  onLogin: (u: User) => void;
  onError: (s: string) => void;
  error: string;
}) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    onError("");
    try {
      const r = await api<{ access_token: string; user: User }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(r.access_token);
      onLogin(r.user);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Не удалось войти");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-page">
      <div className="login-decoration">
        <div className="login-orb orb-one" />
        <div className="login-orb orb-two" />
        <div className="login-copy">
          <div className="brand-mark large">
            <Flame />
          </div>
          <p className="eyebrow">SMART PRODUCTION PLATFORM</p>
          <h1>
            Создавайте
            <br />
            светлые идеи.
          </h1>
          <p>
            Управляйте производством свечей, складом и поставками в одном
            пространстве.
          </p>
          <div className="login-foot">
            CandleFlow AI <span>·</span> Производство с ясностью
          </div>
        </div>
      </div>
      <div className="login-form-side">
        <form className="login-form" onSubmit={submit}>
          <div className="mobile-brand">
            <div className="brand-mark">
              <Flame />
            </div>
            <b>CandleFlow</b>
          </div>
          <span className="eyebrow">С ВОЗВРАЩЕНИЕМ</span>
          <h2>Войти в систему</h2>
          <p className="muted">Введите данные своей учётной записи</p>
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.ru"
            />
          </label>
          <label>
            Пароль
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
            />
          </label>
          {error && <div className="error-box">{error}</div>}
          <button className="primary-btn full" disabled={busy}>
            {busy ? "Входим…" : "Войти в рабочее пространство"}
            <ArrowUpRight size={17} />
          </button>
          <small className="login-hint">
            Для доступа используйте учётную запись backend.
          </small>
        </form>
      </div>
    </div>
  );
}
export default Login;
