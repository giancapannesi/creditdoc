const $ = (id) => document.getElementById(id);
let lastPinId = null;
let isPinterestConnected = false;

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { ok: false, raw: text }; }
  if (!res.ok) throw data;
  return data;
}

function show(data) {
  $("api-output").innerHTML = statusHtml(typeof data === "string" ? data : summarize(data));
}

function summarize(data) {
  if (!data || data.ok === false) {
    return `Status: failed\n${data?.error || "Unknown error"}`;
  }
  if (data.account) {
    return [
      "Status: connected",
      `Account: ${data.account.username || data.account.account_type || "Pinterest account returned"}`,
      "API endpoint: /v5/user_account",
    ].join("\n");
  }
  if (Array.isArray(data.boards)) {
    const names = data.boards.slice(0, 8).map((board) => `- ${board.name || board.id}`).join("\n");
    return [
      "Status: boards fetched",
      `Boards returned: ${data.boards.length}`,
      names || "No boards returned",
      "API endpoint: /v5/boards",
    ].join("\n");
  }
  if (data.id) {
    return `Status: draft saved\nQueue ID: ${data.id}`;
  }
  if (data.result) {
    return `Status: Pinterest POST completed\nPin ID: ${data.result.id || "returned by Pinterest"}`;
  }
  return "Status: complete";
}

function statusHtml(text) {
  const lines = String(text).split("\n").filter(Boolean);
  const first = lines.shift() || "Status: ready";
  const rest = lines.map((line) => `<li>${escapeHtml(line.replace(/^- /, ""))}</li>`).join("");
  return `<strong>${escapeHtml(first)}</strong>${rest ? `<ul>${rest}</ul>` : ""}`;
}

async function savePin() {
  const payload = {
    board_id: $("board").value,
    title: $("title").value,
    description: $("description").value,
    link: $("link").value,
    image_path: $("image-path").value,
    alt_text: $("alt-text").value,
  };
  const data = await api("/api/pins", { method: "POST", body: JSON.stringify(payload) });
  lastPinId = data.id;
  show(data);
  await refreshPins();
  return data.id;
}

async function refreshMe() {
  try {
    const data = await api("/api/me");
    $("connection").textContent = data.pinterest_connected
      ? `Pinterest connected${data.account_username ? `: ${data.account_username}` : ""}`
      : "Pinterest not connected";
    isPinterestConnected = Boolean(data.pinterest_connected);
  } catch (err) {
    $("connection").textContent = "Login required";
  }
}

async function refreshBoards() {
  const data = await api("/api/boards");
  const board = $("board");
  board.innerHTML = "";
  for (const item of data.boards || []) {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = item.name || item.id;
    board.appendChild(opt);
  }
  if (!board.children.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No boards returned";
    board.appendChild(opt);
  }
  show(data);
}

async function refreshPins() {
  const data = await api("/api/pins");
  $("pins").innerHTML = (data.pins || []).map((pin) => `
    <div class="pin-row ${pin.status === "failed" ? "failed" : ""}">
      <div>
        <strong>#${pin.id} · ${escapeHtml(pin.title || "Untitled")}</strong>
        <small>${escapeHtml(pin.status || "")}${pin.pin_id ? ` · Pinterest pin ${escapeHtml(pin.pin_id)}` : ""}</small>
        ${pin.rejection_reason ? `<small>${escapeHtml(pin.rejection_reason)}</small>` : ""}
      </div>
      <small>${escapeHtml(pin.queued_at || "")}</small>
    </div>
  `).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

document.addEventListener("DOMContentLoaded", async () => {
  await refreshMe();

  $("check-account").addEventListener("click", async () => {
    try { show(await api("/api/pinterest/account")); } catch (err) { show(err); }
  });

  $("check-boards").addEventListener("click", async () => {
    try { await refreshBoards(); } catch (err) { show(err); }
  });

  $("connect-token").addEventListener("click", async () => {
    try {
      const token = $("access-token").value.trim();
      const data = await api("/api/connect-token", {
        method: "POST",
        body: JSON.stringify({ access_token: token }),
      });
      $("access-token").value = "";
      show(`Status: connected\nAccount: ${data.account_username || "Pinterest account returned"}\nScopes: ${data.scope || "read access"}`);
      await refreshMe();
      await refreshBoards();
    } catch (err) {
      show(err);
    }
  });

  $("upload").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("image", file);
    const res = await fetch("/api/upload", { method: "POST", body: fd, credentials: "same-origin" });
    const data = await res.json();
    if (data.ok) $("image-path").value = data.image_path;
    show(data);
  });

  $("save-pin").addEventListener("click", async () => {
    try { await savePin(); } catch (err) { show(err); }
  });

  $("post-now").addEventListener("click", async () => {
    try {
      const id = lastPinId || await savePin();
      show(await api(`/api/pins/${id}/post-now`, { method: "POST", body: "{}" }));
      await refreshPins();
    } catch (err) {
      show(err);
      await refreshPins();
    }
  });

  if (isPinterestConnected) {
    try { await refreshBoards(); } catch (err) { show(err); }
  } else {
    show("Status: Pinterest not connected\nClick Connect Pinterest to authorize the app.");
  }
});
