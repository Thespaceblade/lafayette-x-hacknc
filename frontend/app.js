// Laurel Hill Residential — request inbox front-end.
// Loads requests from GET /api/requests (server.py). Falls back to SAMPLE_REQUESTS
// when opened without the server. New requests POST to /api/requests.

// Replay clock from the handbook: "Today is Monday, October 5, 2026, 7:00 AM".
const NOW = new Date("2026-10-05T07:00:00");

const PROPERTIES = ["The Weaver", "Estes Commons", "Pritchard Court", "Merritt Mill Flats", "Church Street Duplexes", "Barclay Townhomes"];

// Problem categories, in priority order. `due` returns the response deadline.
const CATEGORIES = [
  { id: "emergency", label: "Emergency", color: "var(--emergency)", owner: "Luis (919-555-0100) + after-hours vendor", due: d => addHours(d, 1) },
  { id: "urgent",    label: "Urgent repair", color: "var(--urgent)", owner: "Luis", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "fraud",     label: "Bank change / possible fraud", color: "var(--emergency)", owner: "Priya — do not act", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "rent",      label: "Rent & payments", color: "var(--priya)", owner: "Priya", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "legal",     label: "Lease break, sublease & legal", color: "var(--priya)", owner: "Priya", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "esa",       label: "Service & support animals", color: "var(--priya)", owner: "Priya", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "leasing",   label: "Leasing & showings", color: "var(--info)", owner: "Jake (919-555-0102)", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "noise",     label: "Noise", color: "var(--info)", owner: "Log + acknowledge", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
  { id: "routine",   label: "Routine repair", color: "var(--routine)", owner: "Luis (work order)", due: d => endOfBusinessDay(addBusinessDays(d, 5)) },
  { id: "review",    label: "Needs review", color: "var(--review)", owner: "Human review", due: d => endOfBusinessDay(addBusinessDays(d, 1)) },
];
const CAT = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));

// Keyword classifier placeholder. Swap for the real classifier by having the
// server return `category` on each request — the front-end uses it when present.
const RULES = [
  ["emergency", /\b(no heat|heat (is |has )?(not|isn'?t|won'?t|stopped)|heater|furnace|smell(s)? (like )?gas|gas (smell|leak)|huele a gas|carbon monoxide|co alarm|co detector|smoke|fire|flood|sewage|water (is )?(coming|pouring|leaking|dripping) (through|from|in)|ceiling.{0,20}leak|leak.{0,20}ceiling|no power|power (is )?out|won'?t lock|can'?t lock|doesn'?t lock|lock (is )?broken|sin calefacci[oó]n|inundaci[oó]n)\b/i],
  ["fraud", /\b(bank (details|info|account)|routing number|account number|wire|changed banks|new bank|payment details|direct deposit|ach)\b/i],
  ["esa", /\b(emotional support|service animal|esa)\b/i],
  ["legal", /\b(break (my |the )?lease|lease break|sublease|sublet|lawyer|attorney|court|security deposit|evict\w*)\b/i],
  ["rent", /\b(late fee|payment plan|pay (my |full |the )?rent|rent (is |was )?late|can'?t pay|autopay|rent payment|alquiler)\b/i],
  ["urgent", /\b(hot water|fridge|refrigerator|freezer|ac|a\/c|air condition\w*|toilet|locked out|lock(ed)? myself out|lockout)\b/i],
  ["noise", /\b(noise|noisy|loud|music|party|blasting|ruido)\b/i],
  ["leasing", /\b(tour|showing|available|availability|apply|application|move[- ]in|takeover|bedroom|\d ?br|do you allow|pets?|dogs?|cats?|vacanc\w*)\b/i],
  ["routine", /\b(drip\w*|faucet|blinds?|drain|light|bulb|squeak\w*|broken|repair|fix|leak\w*|clog\w*|outlet|door|window|cabinet|disposal)\b/i],
];
function classify(text) {
  for (const [id, re] of RULES) if (re.test(text)) return id;
  return "review";
}
function detectLanguage(text) {
  if (/[ñ¿¡]/i.test(text)) return "es";
  const hits = (text.match(/\b(el|la|los|las|que|qué|en|mi|por|favor|hay|tengo|está|huele|sin|agua|cocina|hola|gracias)\b/gi) || []).length;
  return hits >= 2 ? "es" : "en";
}
function safetyNote(text) {
  if (/(smell(s)? (like )?gas|gas (smell|leak)|huele a gas)/i.test(text))
    return "If you smell gas: leave the unit now. From outside, call 911 and Enbridge Gas North Carolina. Don't flip any switches.";
  if (/(carbon monoxide|co alarm|co detector)/i.test(text))
    return "If a carbon monoxide alarm is sounding: everyone (and any pets) should leave the unit now and call 911 from outside.";
  if (/\b(fire|smoke)\b/i.test(text)) return "If there is fire or smoke: call 911 first.";
  return "This looks like an emergency. For a fast response, also call Luis at 919-555-0100 (any hour).";
}

// ---- Date helpers -------------------------------------------------------
function addHours(d, h) { return new Date(d.getTime() + h * 3600e3); }
function isWeekend(d) { return d.getDay() === 0 || d.getDay() === 6; }
function addBusinessDays(d, n) {
  const r = new Date(d);
  while (n > 0) { r.setDate(r.getDate() + 1); if (!isWeekend(r)) n--; }
  return r;
}
function endOfBusinessDay(d) { const r = new Date(d); r.setHours(17, 0, 0, 0); return r; }
const fmt = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
function fmtDuration(ms) {
  const m = Math.round(ms / 60000);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h}h ${m % 60}m` : `${Math.floor(h / 24)}d ${h % 24}h`;
}

// ---- Sample data (fictional; replaced by data/messages.csv via server.py) ---
const SAMPLE_REQUESTS = [
  { id: "S01", received_at: "2026-10-02T17:42", channel: "sms", sender: "Dana Whitfield", contact: "919-555-0141", property: "Estes Commons", unit: "3C", body: "No heat since this afternoon. It's 58 degrees inside the apartment." },
  { id: "S02", received_at: "2026-10-02T19:05", channel: "email", sender: "Marcus Lee", contact: "mlee@example.com", property: "The Weaver", unit: "", body: "Hi, is there a 2 bedroom at The Weaver available as a takeover? Could I tour Saturday afternoon?" },
  { id: "S03", received_at: "2026-10-02T21:30", channel: "web form", sender: "Tri-County Plumbing Billing", contact: "billing@tricounty-plumb.example", property: "", unit: "", body: "We have changed banks. Please update the routing number and account number on file for all future payments to us." },
  { id: "S04", received_at: "2026-10-03T01:14", channel: "sms", sender: "Ellie Park", contact: "919-555-0177", property: "Pritchard Court", unit: "4", body: "The upstairs neighbors in unit 6 are blasting music again. Third weekend in a row." },
  { id: "S05", received_at: "2026-10-03T08:20", channel: "voicemail", sender: "Sam Ortiz", contact: "919-555-0123", property: "Merritt Mill Flats", unit: "12", body: "Kitchen faucet has been dripping for a few days. Not urgent, whenever someone can come by." },
  { id: "S06", received_at: "2026-10-03T10:47", channel: "sms", sender: "Lucía Moreno", contact: "919-555-0190", property: "Barclay Townhomes", unit: "7", body: "Hola, huele a gas en la cocina desde hace una hora. ¿Qué hago?" },
  { id: "S07", received_at: "2026-10-03T14:02", channel: "email", sender: "Jordan Hayes", contact: "jhayes@example.com", property: "The Weaver", unit: "2B", body: "I'd like to get an emotional support dog. What paperwork do you need from me?" },
  { id: "S08", received_at: "2026-10-03T16:30", channel: "sms", sender: "Ben Carter", contact: "919-555-0155", property: "Church Street Duplexes", unit: "3A", body: "Fridge stopped cooling sometime today, everything in it is warm." },
  { id: "S09", received_at: "2026-10-03T23:55", channel: "sms", sender: "Aisha Khan", contact: "919-555-0168", property: "Estes Commons", unit: "1A", body: "I'm locked out of my apartment, keys are inside. Is anyone available?" },
  { id: "S10", received_at: "2026-10-04T03:10", channel: "voicemail", sender: "Tyler Brooks", contact: "919-555-0132", property: "The Weaver", unit: "5D", body: "Water is coming through the ceiling in the bathroom, it's dripping onto the floor pretty fast." },
  { id: "S11", received_at: "2026-10-04T11:20", channel: "email", sender: "Grace Kim", contact: "gkim@example.com", property: "Merritt Mill Flats", unit: "8", body: "I can't pay my full rent this month. Can I set up a payment plan, and will the late fee still apply?" },
  { id: "S12", received_at: "2026-10-04T15:45", channel: "email", sender: "Noah Patel", contact: "npatel@example.com", property: "Barclay Townhomes", unit: "2", body: "I got a job in Raleigh and need to break my lease in December. What are my options?" },
  { id: "S13", received_at: "2026-10-04T19:12", channel: "web form", sender: "Riley Adams", contact: "radams@example.com", property: "Merritt Mill Flats", unit: "", body: "Do you allow dogs at Merritt Mill Flats? I have a 30 lb lab mix." },
  { id: "S14", received_at: "2026-10-04T22:40", channel: "sms", sender: "Chris Nguyen", contact: "919-555-0109", property: "Pritchard Court", unit: "6", body: "Our CO alarm is going off and won't stop." },
  { id: "S15", received_at: "2026-10-05T06:15", channel: "email", sender: "Maya Johnson", contact: "mjohnson@example.com", property: "Church Street Duplexes", unit: "1B", body: "The bathroom blind is broken and the light over the sink is dead." },
  { id: "S16", received_at: "2026-10-05T06:40", channel: "sms", sender: "Dana Whitfield", contact: "919-555-0141", property: "Estes Commons", unit: "3C", body: "Still no heat. It's 54 degrees in here now." },
];

// ---- State --------------------------------------------------------------
const state = { requests: [], category: "", property: "", query: "", overdueOnly: false, sort: "priority", freshId: null };
const $ = s => document.querySelector(s);

function enrich(r) {
  const received = new Date(r.received_at);
  const category = CAT[r.category] ? r.category : classify(r.body || "");
  const due = CAT[category].due(received);
  return { ...r, receivedDate: received, category, language: r.language || detectLanguage(r.body || ""), due, overdue: due < NOW && !r.isNew };
}
function markFollowUps(list) {
  const seen = new Map();
  [...list].sort((a, b) => a.receivedDate - b.receivedDate).forEach(r => {
    const key = (r.contact || r.sender || "") + "|" + (r.unit || "");
    r.followUp = seen.has(key) ? seen.get(key) : null;
    seen.set(key, r.id);
  });
  return list;
}

async function load() {
  let raw;
  try {
    const res = await fetch("/api/requests");
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    raw = data.source === "sample" ? [...data.requests, ...SAMPLE_REQUESTS] : data.requests;
  } catch { raw = SAMPLE_REQUESTS; }
  state.requests = markFollowUps(raw.map(enrich));
  render();
}

// ---- Rendering ----------------------------------------------------------
function matches(r, ignoreCategory = false) {
  if (!ignoreCategory && state.category && r.category !== state.category) return false;
  if (state.property && r.property !== state.property) return false;
  if (state.overdueOnly && !r.overdue) return false;
  if (state.query) {
    const hay = [r.body, r.sender, r.contact, r.property, r.unit, r.channel].join(" ").toLowerCase();
    if (!hay.includes(state.query.toLowerCase())) return false;
  }
  return true;
}

function renderCategories() {
  const pool = state.requests.filter(r => matches(r, true));
  const items = [{ id: "", label: "All problems", color: "var(--muted)" }, ...CATEGORIES];
  $("#categoryList").innerHTML = items.map(c => {
    const n = c.id ? pool.filter(r => r.category === c.id).length : pool.length;
    return `<li><button data-cat="${c.id}" class="${state.category === c.id ? "active" : ""}">
      <span class="dot" style="background:${c.color}"></span>${c.label}<span class="n">${n}</span></button></li>`;
  }).join("");
}

function esc(s) { return String(s ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch])); }

function renderList() {
  const order = Object.fromEntries(CATEGORIES.map((c, i) => [c.id, i]));
  const list = state.requests.filter(r => matches(r)).sort((a, b) =>
    state.sort === "newest" ? b.receivedDate - a.receivedDate :
    state.sort === "oldest" ? a.receivedDate - b.receivedDate :
    (order[a.category] - order[b.category]) || (b.overdue - a.overdue) || (a.due - b.due));

  $("#count").textContent = `${list.length} request${list.length === 1 ? "" : "s"} · ${list.filter(r => r.overdue).length} overdue`;
  $("#requests").innerHTML = list.length ? list.map(r => {
    const c = CAT[r.category];
    const where = [r.property, r.unit && `Unit ${r.unit}`].filter(Boolean).join(" · ") || "No unit given";
    const dueText = r.overdue
      ? `<span class="overdue">Overdue by ${fmtDuration(NOW - r.due)} as of Mon 7:00 AM</span>`
      : `Respond by ${fmt.format(r.due)}`;
    return `<li class="card ${r.id === state.freshId ? "new" : ""}" style="--c:${c.color}">
      <div class="meta">
        <span class="badge" style="--c:${c.color}">${c.label}</span>
        <span class="who">${esc(r.sender || "Unknown sender")}</span>
        <span>${esc(where)}</span>
        <span>${esc(r.channel || "")} · ${fmt.format(r.receivedDate)}</span>
        ${r.language !== "en" ? `<span class="tag">${esc(r.language.toUpperCase())}</span>` : ""}
        ${r.followUp ? `<span class="tag">Follow-up to ${esc(r.followUp)}</span>` : ""}
      </div>
      <p>${esc(r.body)}</p>
      <div class="foot"><span>Goes to: <strong>${esc(c.owner)}</strong></span><span>${dueText}</span><span>${esc(r.contact || "")}</span></div>
    </li>`;
  }).join("") : `<li class="empty">No requests match these filters.</li>`;
}

function render() { renderCategories(); renderList(); }

// ---- Form ---------------------------------------------------------------
function updateEmergencyNote() {
  const f = $("#requestForm");
  const text = f.elements.body.value;
  const cat = f.elements.category.value || (text.trim() ? classify(text) : "");
  const note = $("#emergencyNote");
  note.hidden = cat !== "emergency";
  if (!note.hidden) note.textContent = safetyNote(text);
}

async function submitRequest(e) {
  e.preventDefault();
  const f = e.target;
  const payload = {
    sender: f.elements.sender.value.trim(), contact: f.elements.contact.value.trim(), property: f.elements.property.value,
    unit: f.elements.unit.value.trim(), body: f.elements.body.value.trim(), channel: "web form",
    category: f.elements.category.value || undefined,
  };
  let saved;
  try {
    const res = await fetch("/api/requests", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!res.ok) throw new Error(res.status);
    saved = await res.json();
  } catch {
    saved = { ...payload, id: "N" + (state.requests.length + 1), received_at: new Date().toISOString() };
  }
  const r = enrich({ ...saved, isNew: true });
  state.requests = markFollowUps([r, ...state.requests]);
  state.freshId = r.id;
  state.category = ""; state.sort = "newest"; $("#sort").value = "newest";
  f.reset(); $("#emergencyNote").hidden = true;
  $("#formDialog").close();
  render();
}

// ---- Wire up ------------------------------------------------------------
function init() {
  $("#asOf").textContent = "Mon, Oct 5, 2026 7:00 AM (replay)";
  const propOpts = PROPERTIES.map(p => `<option>${p}</option>`).join("");
  $("#propertyFilter").insertAdjacentHTML("beforeend", propOpts);
  $("#formProperty").insertAdjacentHTML("beforeend", propOpts);
  $("#formCategory").insertAdjacentHTML("beforeend",
    CATEGORIES.filter(c => c.id !== "review").map(c => `<option value="${c.id}">${c.label}</option>`).join(""));

  $("#categoryList").addEventListener("click", e => {
    const b = e.target.closest("button[data-cat]"); if (!b) return;
    state.category = b.dataset.cat; render();
  });
  $("#propertyFilter").addEventListener("change", e => { state.property = e.target.value; render(); });
  $("#search").addEventListener("input", e => { state.query = e.target.value.trim(); render(); });
  $("#overdueOnly").addEventListener("change", e => { state.overdueOnly = e.target.checked; render(); });
  $("#sort").addEventListener("change", e => { state.sort = e.target.value; renderList(); });

  $("#newBtn").addEventListener("click", () => $("#formDialog").showModal());
  $("#cancelBtn").addEventListener("click", () => $("#formDialog").close());
  $("#requestForm").addEventListener("submit", submitRequest);
  $("#requestForm").elements.body.addEventListener("input", updateEmergencyNote);
  $("#requestForm").elements.category.addEventListener("change", updateEmergencyNote);

  load();
}
init();
