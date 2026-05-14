import { useState } from "react";
import type { AICommand, AIPlanResponse } from "@/lib/ai-schema";
import { aiCommand } from "@/api/sales-client";

const SUGGESTIONS: { cmd: AICommand; label: string; example: string }[] = [
  { cmd: "goal", label: "/goal", example: "Tạo kế hoạch 30 ngày cho LI3BR, ưu tiên CP prio 1" },
  { cmd: "optimize", label: "/optimize", example: "Tối ưu để không PR nào làm quá 6 ngày/tuần" },
  { cmd: "risk", label: "/risk", example: "Phát hiện campaign có nguy cơ không đạt" },
  { cmd: "recover", label: "/recover", example: "Lập kế hoạch bù cho BC LI3BC12 chỉ đạt 40%" },
  { cmd: "simulate", label: "/simulate", example: "Nếu tăng 5 PR, kết quả ra sao?" },
  { cmd: "explain", label: "/explain", example: "Vì sao CP01 được xếp trước CP15?" },
  { cmd: "daily", label: "/daily", example: "Hôm nay triển khai nhóm nào, ở đâu?" },
];

function parseInput(text: string): { command: AICommand; prompt: string } {
  const m = text.trim().match(/^\/(\w+)\s*(.*)$/);
  if (m && SUGGESTIONS.some(s => s.cmd === m[1])) {
    return { command: m[1] as AICommand, prompt: m[2] || "" };
  }
  return { command: "goal", prompt: text };
}

interface Props {
  campaignId?: number;
  onResult: (resp: AIPlanResponse) => void;
}

export default function AICommandBar({ campaignId, onResult }: Props) {
  const [text, setText] = useState("/goal Tạo kế hoạch 30 ngày, ưu tiên prioridad 1");
  const [loading, setLoading] = useState(false);
  const [showSuggest, setShowSuggest] = useState(false);

  const run = async () => {
    const { command, prompt } = parseInput(text);
    setLoading(true);
    try {
      const resp = await aiCommand({ command, prompt, campaign_id: campaignId });
      onResult(resp);
    } catch (e: any) {
      alert("AI command failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: "relative", borderBottom: "1px solid #e5e7eb", padding: 8, background: "#f8fafc" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ fontSize: 18 }}>🤖</span>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onFocus={() => setShowSuggest(true)}
          onBlur={() => setTimeout(() => setShowSuggest(false), 200)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="/goal Tạo kế hoạch …  •  /optimize, /risk, /recover, /simulate, /explain, /daily"
          style={{
            flex: 1, padding: "8px 12px", borderRadius: 6, border: "1px solid #cbd5e1",
            fontSize: 13, fontFamily: "ui-monospace, monospace",
          }}
        />
        <button className="primary" disabled={loading} onClick={run}>
          {loading ? "AI đang suy nghĩ…" : "🚀 Run"}
        </button>
      </div>
      {showSuggest && (
        <div style={{
          position: "absolute", top: "100%", left: 8, right: 8, zIndex: 50,
          background: "white", border: "1px solid #e5e7eb", borderRadius: 6,
          boxShadow: "0 6px 24px rgba(0,0,0,0.08)", padding: 6, marginTop: 4,
        }}>
          {SUGGESTIONS.map((s) => (
            <div
              key={s.cmd}
              onMouseDown={() => setText(`${s.label} ${s.example}`)}
              style={{
                padding: "6px 10px", borderRadius: 4, cursor: "pointer", fontSize: 12,
                display: "flex", justifyContent: "space-between",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f1f5f9")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <code style={{ fontWeight: 600 }}>{s.label}</code>
              <span style={{ color: "#6b7280" }}>{s.example}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
