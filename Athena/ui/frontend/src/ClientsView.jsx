// ClientsView.jsx — Phase 2C Client Lifecycle
// Intake form, engagement tracker, SOW + regulatory assessment triggers.

import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000";

const C = {
  navy:  "#0A2540", ocean: "#1A6FA3", gold: "#C4922A",
  teal:  "#1F7A6D", cloud: "#F8FAFC", sand: "#F2EDE6",
  pearl: "#FFFFFF", ink:   "#0A2540", slate: "#3C5470",
  fog:   "#7B90A0", mist:  "#DDE4EB", red:  "#C0392B",
  green: "#1F7A6D",
};

const F = { sans: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" };

const S = {
  card:    { background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 10,
             padding: "20px 24px", marginBottom: 16, boxShadow: "0 1px 4px rgba(10,37,64,0.04)" },
  label:   { fontFamily: F.sans, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em",
             textTransform: "uppercase", color: C.fog, marginBottom: 5, display: "block" },
  input:   { width: "100%", padding: "8px 12px", border: `1px solid ${C.mist}`, borderRadius: 7,
             fontFamily: F.sans, fontSize: 13, background: C.pearl, color: C.slate,
             outline: "none", boxSizing: "border-box" },
  textarea:{ width: "100%", padding: "9px 12px", border: `1px solid ${C.mist}`, borderRadius: 7,
             fontFamily: F.sans, fontSize: 13, background: C.pearl, color: C.slate,
             outline: "none", resize: "vertical", boxSizing: "border-box", minHeight: 72 },
  btn:     (v="primary") => ({
    padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer",
    fontFamily: F.sans, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em",
    textTransform: "uppercase", transition: "opacity 0.15s",
    background: v==="primary" ? C.navy : v==="teal" ? C.teal : v==="ocean" ? C.ocean
              : v==="gold" ? C.gold : v==="red" ? C.red : "transparent",
    color: v==="ghost" ? C.fog : C.pearl,
    border: v==="ghost" ? `1px solid ${C.mist}` : "none",
  }),
  h2: { fontSize: 16, fontWeight: 600, color: C.ink, margin: "0 0 4px", fontFamily: F.sans },
  h3: { fontSize: 13, fontWeight: 600, color: C.slate, margin: "0 0 12px", fontFamily: F.sans },
  stat: { fontFamily: F.sans, fontSize: 22, fontWeight: 700, color: C.ink, lineHeight: 1 },
};

const STATUS_COLORS = {
  prospect:    { bg: "#EBF3FB", text: C.ocean },
  in_discussion:{ bg: "#FEF3E2", text: C.gold },
  active:      { bg: "#E8F5F1", text: C.teal },
  completed:   { bg: "#F0F0F0", text: C.fog },
  lost:        { bg: "#FDECEA", text: C.red },
};

const ENGAGEMENT_STATUS_COLORS = {
  scoping:          { bg: "#EBF3FB", text: C.ocean },
  sow_generated:    { bg: "#FEF3E2", text: C.gold },
  active:           { bg: "#E8F5F1", text: C.teal },
  deliverable_ready:{ bg: "#E8F5F1", text: C.teal },
  completed:        { bg: "#F0F0F0", text: C.fog },
  cancelled:        { bg: "#FDECEA", text: C.red },
};

const PROGRAM_TIERS = [
  { value: "",                  label: "Select program..." },
  { value: "career_prep",       label: "Career Prep — $699" },
  { value: "early_career",      label: "Early Career QA/RA — $1,499" },
  { value: "mid_career",        label: "Mid-Career Acceleration — $1,899" },
  { value: "career_transition", label: "Career Transition — $2,299" },
  { value: "consulting_gap",    label: "Regulatory Gap Assessment — $4,500" },
  { value: "consulting_strategy",label:"Regulatory Strategy Engagement — $8,500" },
  { value: "custom",            label: "Custom Engagement" },
];

const CLIENT_STATUSES = ["prospect", "in_discussion", "active", "completed", "lost"];

function StatusBadge({ status, map = STATUS_COLORS, label }) {
  const col = map[status] || { bg: "#F0F0F0", text: C.fog };
  return (
    <span style={{ background: col.bg, color: col.text, borderRadius: 20,
      padding: "2px 10px", fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
      textTransform: "uppercase", fontFamily: F.sans }}>
      {label || status.replace(/_/g, " ")}
    </span>
  );
}

function EmptyState({ icon, title, subtitle }) {
  return (
    <div style={{ textAlign: "center", padding: "48px 24px", color: C.fog }}>
      <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>{icon}</div>
      <div style={{ fontFamily: F.sans, fontSize: 14, fontWeight: 600, color: C.slate,
        marginBottom: 6 }}>{title}</div>
      <div style={{ fontFamily: F.sans, fontSize: 12 }}>{subtitle}</div>
    </div>
  );
}

// ── Intake Form ───────────────────────────────────────────────────────────────
function IntakeForm({ onCreated, onCancel }) {
  const [form, setForm] = useState({
    name: "", org: "", role: "", email: "", phone: "",
    program_tier: "", regulatory_challenge: "", timeline: "",
    budget_range: "", notes: "", status: "prospect",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError]   = useState("");

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError("Client name is required."); return; }
    setSaving(true); setError("");
    try {
      const res = await fetch(`${API}/api/clients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.client_id) onCreated(data.client_id);
      else setError("Failed to create client.");
    } catch {
      setError("Connection error — is Athena running?");
    } finally {
      setSaving(false);
    }
  };

  const field = (label, key, type="text", opts={}) => (
    <div style={{ marginBottom: 14 }}>
      <label style={S.label}>{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={e => set(key, e.target.value)}
        style={S.input}
        {...opts}
      />
    </div>
  );

  return (
    <form onSubmit={submit}>
      <div style={{ ...S.card, borderLeft: `3px solid ${C.ocean}` }}>
        <div style={{ ...S.h3, marginBottom: 20 }}>New Client Intake</div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
          {field("Full Name *", "name", "text", { placeholder: "Jane Smith", autoFocus: true })}
          {field("Organization", "org", "text", { placeholder: "Acme MedTech Inc." })}
          {field("Role / Title", "role", "text", { placeholder: "Director of Regulatory Affairs" })}
          {field("Email", "email", "email", { placeholder: "jane@acmemedtech.com" })}
          {field("Phone", "phone", "tel", { placeholder: "+1 (858) 555-0100" })}
          <div style={{ marginBottom: 14 }}>
            <label style={S.label}>Program / Tier</label>
            <select value={form.program_tier} onChange={e => set("program_tier", e.target.value)}
              style={{ ...S.input, height: 36 }}>
              {PROGRAM_TIERS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={S.label}>Regulatory Challenge</label>
          <textarea value={form.regulatory_challenge}
            onChange={e => set("regulatory_challenge", e.target.value)}
            placeholder="What specific regulatory challenge are they facing? (e.g. 510(k) submission for Class II combination product, no existing QMS)"
            style={S.textarea}/>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
          {field("Timeline", "timeline", "text", { placeholder: "e.g. Needs to be FDA-ready by Q4 2026" })}
          {field("Budget Range", "budget_range", "text", { placeholder: "e.g. $2K–$5K" })}
        </div>

        <div style={{ marginBottom: 14 }}>
          <label style={S.label}>Notes</label>
          <textarea value={form.notes} onChange={e => set("notes", e.target.value)}
            placeholder="How did we meet? Any context from discovery call..."
            style={{ ...S.textarea, minHeight: 56 }}/>
        </div>

        {error && (
          <div style={{ color: C.red, fontFamily: F.sans, fontSize: 12, marginBottom: 12 }}>
            {error}
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          <button type="submit" style={S.btn("primary")} disabled={saving}>
            {saving ? "Saving..." : "Create Client"}
          </button>
          <button type="button" style={S.btn("ghost")} onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </form>
  );
}

// ── Engagement Panel ──────────────────────────────────────────────────────────
function EngagementPanel({ client, runningAgents }) {
  const [engagements, setEngagements] = useState([]);
  const [adding, setAdding]           = useState(false);
  const [newTitle, setNewTitle]       = useState("");
  const [newDesc, setNewDesc]         = useState("");
  const [running, setRunning]         = useState(false);
  const [toast, setToast]             = useState("");

  const load = useCallback(() => {
    fetch(`${API}/api/clients/${client.id}/engagements`)
      .then(r => r.json()).then(d => setEngagements(d.engagements || []))
      .catch(() => {});
  }, [client.id]);

  useEffect(() => { load(); }, [load]);

  const addEngagement = async () => {
    if (!newTitle.trim()) return;
    await fetch(`${API}/api/clients/${client.id}/engagements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle, description: newDesc, status: "scoping" }),
    });
    setAdding(false); setNewTitle(""); setNewDesc("");
    load();
  };

  const triggerSOW = async (engId = null) => {
    setRunning(true);
    setToast("SOW generation started — check Review Queue when complete.");
    await fetch(`${API}/api/agents/sow`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: client.id, engagement_id: engId }),
    });
    setTimeout(() => { setRunning(false); setToast(""); load(); }, 3000);
  };

  const triggerAssessment = async () => {
    if (!client.regulatory_challenge) {
      setToast("Add a regulatory challenge to the client intake before running an assessment.");
      setTimeout(() => setToast(""), 4000);
      return;
    }
    setRunning(true);
    setToast("Regulatory gap assessment started — check Review Queue when complete.");
    await fetch(`${API}/api/agents/regulatory-assessment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_type: client.regulatory_challenge,
        classification: "To be confirmed",
        markets: ["US"],
        qms_state: "Current QMS state to be assessed",
        context: `Client: ${client.name}, ${client.org || ""}`,
        client_id: client.id,
      }),
    });
    setTimeout(() => { setRunning(false); setToast(""); load(); }, 3000);
  };

  const agentRunning = runningAgents?.has?.("sow_agent") ||
                       runningAgents?.has?.("regulatory_strategy_agent");

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: 14 }}>
        <div style={S.h3}>Engagements</div>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={S.btn("ghost")} onClick={() => setAdding(a => !a)}>+ Add</button>
          <button style={S.btn("teal")} onClick={() => triggerSOW()} disabled={running || agentRunning}>
            Generate SOW
          </button>
          <button style={S.btn("ocean")} onClick={triggerAssessment} disabled={running || agentRunning}>
            Gap Assessment
          </button>
        </div>
      </div>

      {toast && (
        <div style={{ background: "#E8F5F1", border: `1px solid ${C.teal}`, borderRadius: 7,
          padding: "8px 14px", fontFamily: F.sans, fontSize: 12, color: C.teal, marginBottom: 12 }}>
          {toast}
        </div>
      )}

      {adding && (
        <div style={{ ...S.card, borderLeft: `3px solid ${C.gold}`, marginBottom: 12 }}>
          <div style={{ marginBottom: 10 }}>
            <label style={S.label}>Engagement Title</label>
            <input value={newTitle} onChange={e => setNewTitle(e.target.value)}
              placeholder="e.g. 510(k) Readiness Assessment"
              style={S.input} autoFocus/>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={S.label}>Description</label>
            <textarea value={newDesc} onChange={e => setNewDesc(e.target.value)}
              placeholder="Scope and objectives..."
              style={{ ...S.textarea, minHeight: 56 }}/>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={S.btn("primary")} onClick={addEngagement}>Add</button>
            <button style={S.btn("ghost")} onClick={() => setAdding(false)}>Cancel</button>
          </div>
        </div>
      )}

      {engagements.length === 0 && !adding && (
        <EmptyState icon="📋" title="No engagements yet"
          subtitle='Use "Generate SOW" to create the first engagement, or add one manually.'/>
      )}

      {engagements.map(eng => {
        const sc = ENGAGEMENT_STATUS_COLORS[eng.status] || { bg: "#F0F0F0", text: C.fog };
        return (
          <div key={eng.id} style={{ ...S.card, padding: "14px 18px" }}>
            <div style={{ display: "flex", alignItems: "flex-start",
              justifyContent: "space-between", gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: F.sans, fontSize: 13, fontWeight: 600,
                  color: C.ink, marginBottom: 4 }}>{eng.title}</div>
                {eng.description && (
                  <div style={{ fontFamily: F.sans, fontSize: 12, color: C.slate,
                    marginBottom: 6 }}>{eng.description}</div>
                )}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                  <StatusBadge status={eng.status} map={ENGAGEMENT_STATUS_COLORS}/>
                  {eng.value_usd && (
                    <span style={{ fontFamily: F.sans, fontSize: 11, color: C.teal,
                      fontWeight: 600 }}>${eng.value_usd.toLocaleString()}</span>
                  )}
                  {eng.start_date && (
                    <span style={{ fontFamily: F.sans, fontSize: 11, color: C.fog }}>
                      {eng.start_date}{eng.end_date ? ` → ${eng.end_date}` : ""}
                    </span>
                  )}
                </div>
                {eng.sow_path && (
                  <div style={{ marginTop: 6, fontFamily: F.sans, fontSize: 11, color: C.ocean }}>
                    SOW: {eng.sow_path.split(/[/\\]/).pop()}
                  </div>
                )}
              </div>
              {eng.sow_path === null && (
                <button style={S.btn("ghost")} onClick={() => triggerSOW(eng.id)}
                  disabled={running || agentRunning}>
                  Generate SOW
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Client Detail Panel ───────────────────────────────────────────────────────
function ClientDetail({ client, onUpdate, onDelete, runningAgents }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm]       = useState({ ...client });
  const [saving, setSaving]   = useState(false);
  const [tab, setTab]         = useState("overview");

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/api/clients/${client.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSaving(false);
    setEditing(false);
    onUpdate();
  };

  const del = async () => {
    if (!window.confirm(`Delete client "${client.name}"? This cannot be undone.`)) return;
    await fetch(`${API}/api/clients/${client.id}`, { method: "DELETE" });
    onDelete();
  };

  const tierLabel = PROGRAM_TIERS.find(t => t.value === client.program_tier)?.label || client.program_tier || "—";

  return (
    <div>
      {/* Header */}
      <div style={{ ...S.card, borderLeft: `3px solid ${C.ocean}`, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "flex-start",
          justifyContent: "space-between", gap: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <div style={{ ...S.h2 }}>{client.name}</div>
              <StatusBadge status={client.status}/>
            </div>
            {client.org && (
              <div style={{ fontFamily: F.sans, fontSize: 13, color: C.slate,
                marginBottom: 2 }}>{client.org}</div>
            )}
            {client.role && (
              <div style={{ fontFamily: F.sans, fontSize: 12, color: C.fog }}>{client.role}</div>
            )}
            <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
              {client.email && <a href={`mailto:${client.email}`}
                style={{ fontFamily: F.sans, fontSize: 12, color: C.ocean }}>{client.email}</a>}
              {client.phone && <span style={{ fontFamily: F.sans, fontSize: 12,
                color: C.fog }}>{client.phone}</span>}
              {client.program_tier && <span style={{ fontFamily: F.sans, fontSize: 12,
                color: C.teal, fontWeight: 600 }}>{tierLabel}</span>}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={S.btn("ghost")} onClick={() => setEditing(e => !e)}>Edit</button>
            <button style={S.btn("red")} onClick={del}>Delete</button>
          </div>
        </div>
      </div>

      {/* Edit form */}
      {editing && (
        <div style={{ ...S.card, borderLeft: `3px solid ${C.gold}`, marginBottom: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px" }}>
            {["name","org","role","email","phone"].map(k => (
              <div key={k} style={{ marginBottom: 12 }}>
                <label style={S.label}>{k.charAt(0).toUpperCase() + k.slice(1)}</label>
                <input value={form[k] || ""} onChange={e => set(k, e.target.value)} style={S.input}/>
              </div>
            ))}
            <div style={{ marginBottom: 12 }}>
              <label style={S.label}>Status</label>
              <select value={form.status || "prospect"} onChange={e => set("status", e.target.value)}
                style={{ ...S.input, height: 36 }}>
                {CLIENT_STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g," ")}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={S.label}>Program Tier</label>
              <select value={form.program_tier || ""} onChange={e => set("program_tier", e.target.value)}
                style={{ ...S.input, height: 36 }}>
                {PROGRAM_TIERS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={S.label}>Regulatory Challenge</label>
            <textarea value={form.regulatory_challenge || ""} onChange={e => set("regulatory_challenge", e.target.value)}
              style={{ ...S.textarea, minHeight: 60 }}/>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 20px", marginBottom: 12 }}>
            <div>
              <label style={S.label}>Timeline</label>
              <input value={form.timeline || ""} onChange={e => set("timeline", e.target.value)} style={S.input}/>
            </div>
            <div>
              <label style={S.label}>Budget Range</label>
              <input value={form.budget_range || ""} onChange={e => set("budget_range", e.target.value)} style={S.input}/>
            </div>
          </div>
          <div style={{ marginBottom: 14 }}>
            <label style={S.label}>Notes</label>
            <textarea value={form.notes || ""} onChange={e => set("notes", e.target.value)}
              style={{ ...S.textarea, minHeight: 56 }}/>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={S.btn("primary")} onClick={save} disabled={saving}>
              {saving ? "Saving..." : "Save"}
            </button>
            <button style={S.btn("ghost")} onClick={() => { setEditing(false); setForm({...client}); }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 16, borderBottom: `1px solid ${C.mist}` }}>
        {["overview", "engagements"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: "8px 14px", background: "transparent", border: "none",
            borderBottom: tab === t ? `2px solid ${C.ocean}` : "2px solid transparent",
            cursor: "pointer", fontFamily: F.sans, fontSize: 12, fontWeight: tab === t ? 600 : 400,
            color: tab === t ? C.ocean : C.fog, transition: "all 0.12s", marginBottom: -1,
          }}>{t.charAt(0).toUpperCase() + t.slice(1)}</button>
        ))}
      </div>

      {tab === "overview" && (
        <div>
          {client.regulatory_challenge && (
            <div style={S.card}>
              <div style={S.h3}>Regulatory Challenge</div>
              <div style={{ fontFamily: F.sans, fontSize: 13, color: C.slate, lineHeight: 1.6 }}>
                {client.regulatory_challenge}
              </div>
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            {[
              { label: "Timeline",      value: client.timeline },
              { label: "Budget Range",  value: client.budget_range },
              { label: "Program",       value: tierLabel },
            ].map(({ label, value }) => value ? (
              <div key={label} style={S.card}>
                <div style={S.label}>{label}</div>
                <div style={{ fontFamily: F.sans, fontSize: 13, color: C.ink,
                  fontWeight: 500 }}>{value}</div>
              </div>
            ) : null)}
          </div>
          {client.notes && (
            <div style={{ ...S.card, marginTop: 12 }}>
              <div style={S.h3}>Notes</div>
              <div style={{ fontFamily: F.sans, fontSize: 13, color: C.slate,
                lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{client.notes}</div>
            </div>
          )}
        </div>
      )}

      {tab === "engagements" && (
        <EngagementPanel client={client} runningAgents={runningAgents}/>
      )}
    </div>
  );
}

// ── Main ClientsView ──────────────────────────────────────────────────────────
export default function ClientsView({ runningAgents }) {
  const [clients, setClients]       = useState([]);
  const [selected, setSelected]     = useState(null);
  const [showIntake, setShowIntake] = useState(false);
  const [filterStatus, setFilter]   = useState("");
  const [search, setSearch]         = useState("");
  const [loading, setLoading]       = useState(true);

  const load = useCallback(() => {
    fetch(`${API}/api/clients`)
      .then(r => r.json())
      .then(d => { setClients(d.clients || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const onCreated = (id) => {
    setShowIntake(false);
    load();
    setTimeout(() => {
      fetch(`${API}/api/clients/${id}`).then(r => r.json()).then(setSelected);
    }, 300);
  };

  const filtered = clients.filter(c => {
    if (filterStatus && c.status !== filterStatus) return false;
    if (search) {
      const q = search.toLowerCase();
      return (c.name || "").toLowerCase().includes(q) ||
             (c.org  || "").toLowerCase().includes(q) ||
             (c.role || "").toLowerCase().includes(q);
    }
    return true;
  });

  const statusCounts = clients.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1; return acc;
  }, {});

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center",
        justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 17, fontWeight: 600, color: "#0A2540",
            margin: "0 0 4px", fontFamily: F.sans }}>Clients</h2>
          <div style={{ fontFamily: F.sans, fontSize: 12, color: C.fog }}>
            Intake, engagement tracking, SOW generation
          </div>
        </div>
        <button style={S.btn("primary")} onClick={() => { setShowIntake(true); setSelected(null); }}>
          + New Client
        </button>
      </div>

      {/* Stats row */}
      {clients.length > 0 && (
        <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
          {[
            { label: "Total", count: clients.length, color: C.navy },
            { label: "Prospects", count: statusCounts.prospect || 0, color: C.ocean },
            { label: "In Discussion", count: statusCounts.in_discussion || 0, color: C.gold },
            { label: "Active", count: statusCounts.active || 0, color: C.teal },
          ].map(({ label, count, color }) => (
            <div key={label} style={{ ...S.card, padding: "12px 18px", flex: 1, marginBottom: 0 }}>
              <div style={{ ...S.stat, color, fontSize: 24 }}>{count}</div>
              <div style={{ fontFamily: F.sans, fontSize: 10, color: C.fog,
                letterSpacing: "0.08em", textTransform: "uppercase", marginTop: 3 }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {showIntake && (
        <IntakeForm onCreated={onCreated} onCancel={() => setShowIntake(false)}/>
      )}

      <div style={{ display: "flex", gap: 20 }}>
        {/* Client list */}
        <div style={{ width: 280, flexShrink: 0 }}>
          {/* Filters */}
          <div style={{ marginBottom: 12 }}>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search clients..."
              style={{ ...S.input, marginBottom: 8 }}
            />
            <select value={filterStatus} onChange={e => setFilter(e.target.value)}
              style={{ ...S.input, height: 34, fontSize: 12 }}>
              <option value="">All statuses</option>
              {CLIENT_STATUSES.map(s => (
                <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          {loading && (
            <div style={{ fontFamily: F.sans, fontSize: 12, color: C.fog, padding: "12px 0" }}>
              Loading...
            </div>
          )}

          {!loading && filtered.length === 0 && (
            <EmptyState icon="👤" title="No clients yet"
              subtitle="Click &quot;+ New Client&quot; to add your first intake."/>
          )}

          {filtered.map(c => {
            const sc = STATUS_COLORS[c.status] || { bg: "#F0F0F0", text: C.fog };
            const isSelected = selected?.id === c.id;
            return (
              <div key={c.id}
                onClick={() => { setSelected(c); setShowIntake(false); }}
                style={{
                  padding: "12px 14px", borderRadius: 8, marginBottom: 6, cursor: "pointer",
                  background: isSelected ? C.ocean : C.pearl,
                  border: `1px solid ${isSelected ? C.ocean : C.mist}`,
                  transition: "all 0.12s",
                }}>
                <div style={{ fontFamily: F.sans, fontSize: 13, fontWeight: 600,
                  color: isSelected ? C.pearl : C.ink, marginBottom: 3 }}>{c.name}</div>
                {c.org && <div style={{ fontFamily: F.sans, fontSize: 11,
                  color: isSelected ? "rgba(255,255,255,0.7)" : C.fog }}>{c.org}</div>}
                <div style={{ marginTop: 6 }}>
                  <span style={{
                    background: isSelected ? "rgba(255,255,255,0.2)" : sc.bg,
                    color: isSelected ? C.pearl : sc.text,
                    borderRadius: 20, padding: "1px 8px",
                    fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                    textTransform: "uppercase", fontFamily: F.sans,
                  }}>{c.status.replace(/_/g, " ")}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Detail panel */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selected && !showIntake && (
            <EmptyState icon="👤" title="Select a client"
              subtitle="Choose a client from the list, or add a new one."/>
          )}
          {selected && !showIntake && (
            <ClientDetail
              key={selected.id}
              client={selected}
              runningAgents={runningAgents}
              onUpdate={() => {
                load();
                fetch(`${API}/api/clients/${selected.id}`)
                  .then(r => r.json()).then(setSelected);
              }}
              onDelete={() => { setSelected(null); load(); }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
