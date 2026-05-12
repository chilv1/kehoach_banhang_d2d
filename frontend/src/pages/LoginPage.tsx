import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "@/api/client";

export default function LoginPage() {
  const nav = useNavigate();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setErr(null);
    try {
      if (tab === "register") {
        await register({ username: u, password: p, full_name: name });
      }
      const r = await login(u, p);
      localStorage.setItem("token", r.access_token);
      localStorage.setItem("user", JSON.stringify(r.user));
      nav("/");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || e.message);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 360, margin: "60px auto" }}>
      <div className="card" style={{ padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>{tab === "login" ? "🔐 Đăng nhập" : "📝 Đăng ký"}</h2>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button className={tab === "login" ? "primary" : ""} onClick={() => setTab("login")}>Login</button>
          <button className={tab === "register" ? "primary" : ""} onClick={() => setTab("register")}>Register</button>
        </div>
        {tab === "register" && (
          <div style={{ marginBottom: 8 }}>
            <input placeholder="Họ tên" value={name} onChange={(e) => setName(e.target.value)} style={{ width: "100%" }} />
          </div>
        )}
        <div style={{ marginBottom: 8 }}>
          <input placeholder="Username" value={u} onChange={(e) => setU(e.target.value)} style={{ width: "100%" }} />
        </div>
        <div style={{ marginBottom: 12 }}>
          <input placeholder="Password" type="password" value={p} onChange={(e) => setP(e.target.value)}
                  style={{ width: "100%" }}
                  onKeyDown={(e) => e.key === "Enter" && submit()} />
        </div>
        {err && <div style={{ color: "#dc2626", marginBottom: 8 }}>{err}</div>}
        <button className="primary" onClick={submit} style={{ width: "100%" }}>
          {tab === "login" ? "Đăng nhập" : "Tạo tài khoản & đăng nhập"}
        </button>
      </div>
    </div>
  );
}
