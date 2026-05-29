/* ══════════════════════════════════════════════════════
   dashboard.js — Insta Tracker
   Usa SSE (/api/stats/stream) para progresso em tempo real
══════════════════════════════════════════════════════ */

/* ── Helpers ── */
const AVATAR_COLORS = [
  { bg: '#faeeda', fg: '#854f0b' },
  { bg: '#fbeaf0', fg: '#993556' },
  { bg: '#e6f1fb', fg: '#185fa5' },
  { bg: '#eaf3de', fg: '#3b6d11' },
  { bg: '#eeedfe', fg: '#533ab7' },
  { bg: '#e1f5ee', fg: '#0f6e56' },
  { bg: '#faece7', fg: '#993c1d' },
];

function initials(name) {
  return (name || '?')
    .split(' ')
    .slice(0, 2)
    .map(w => w[0] || '')
    .join('')
    .toUpperCase();
}

function colorFor(index) {
  return AVATAR_COLORS[index % AVATAR_COLORS.length];
}

function fmt(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace('.0', '') + 'M';
  if (n >= 1000)    return (n / 1000).toFixed(1).replace('.0', '') + 'k';
  return String(n);
}

function setEl(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}


/* ══════════════════════════════════════════════════════
   PROGRESS OVERLAY
══════════════════════════════════════════════════════ */

function createOverlay() {
  const ov = document.createElement('div');
  ov.id = 'progress-overlay';
  ov.className = 'progress-overlay';
  ov.innerHTML = `
    <div class="progress-logo">
      <i class="ti ti-brand-instagram"></i>
    </div>
    <div class="progress-texts">
      <div class="progress-label" id="prog-label">Iniciando…</div>
      <div class="progress-sublabel" id="prog-sub">Aguarde um momento</div>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-track">
        <div class="progress-fill" id="prog-fill"></div>
      </div>
      <div class="progress-pct" id="prog-pct">0%</div>
    </div>
    <div class="progress-steps">
      <div class="progress-dot" id="prog-dot-0"></div>
      <div class="progress-dot" id="prog-dot-1"></div>
      <div class="progress-dot" id="prog-dot-2"></div>
      <div class="progress-dot" id="prog-dot-3"></div>
    </div>
  `;
  return ov;
}

const STEP_THRESHOLDS = [0, 30, 65, 88];

function showOverlay() {
  let ov = document.getElementById('progress-overlay');
  if (!ov) {
    // Insere como primeiro filho do body (cobre tudo)
    ov = createOverlay();
    document.body.appendChild(ov);
  }
  ov.classList.remove('hidden');
  updateOverlay(5, 'Iniciando…', 'Conectando ao servidor');
}

function hideOverlay() {
  const ov = document.getElementById('progress-overlay');
  if (ov) {
    ov.style.opacity = '0';
    setTimeout(() => {
      ov.classList.add('hidden');
      ov.style.opacity = '';
    }, 350);
  }
}

const STEP_SUBS = [
  'Verificando sessão',
  'Isso pode levar alguns segundos',
  'Quase lá',
  'Comparando listas',
];

function updateOverlay(pct, label, sub) {
  const fill  = document.getElementById('prog-fill');
  const lbl   = document.getElementById('prog-label');
  const sublbl = document.getElementById('prog-sub');
  const pctEl = document.getElementById('prog-pct');

  if (fill)   fill.style.width   = pct + '%';
  if (lbl)    lbl.textContent    = label;
  if (pctEl)  pctEl.textContent  = Math.round(pct) + '%';

  // Sub-label automático baseado nos thresholds
  const stepIdx = STEP_THRESHOLDS.reduce((acc, t, i) => pct >= t ? i : acc, 0);
  if (sublbl) sublbl.textContent = sub || STEP_SUBS[stepIdx] || '';

  // Atualiza dots
  STEP_THRESHOLDS.forEach((t, i) => {
    const dot = document.getElementById('prog-dot-' + i);
    if (!dot) return;
    if (pct >= t + 20 || (i < stepIdx))      dot.className = 'progress-dot done';
    else if (i === stepIdx)                   dot.className = 'progress-dot active';
    else                                      dot.className = 'progress-dot';
  });
}


/* ══════════════════════════════════════════════════════
   RENDER LISTS
══════════════════════════════════════════════════════ */

function renderList(containerId, users, actionLabel, actionRoute) {
  const el = document.getElementById(containerId);
  if (!el) return;

  if (!users || users.length === 0) {
    el.innerHTML = '<div class="list-loading">Nenhum usuário encontrado.</div>';
    return;
  }

  el.innerHTML = users.map((u, i) => {
    const c   = colorFor(i);
    const ini = initials(u.full_name || u.username);
    return `
      <div class="user-row" id="row-${u.username}">
        <div class="u-avatar" style="background:${c.bg};color:${c.fg}">${ini}</div>
        <div class="u-info">
          <div class="u-name">${u.full_name || u.username}</div>
          <div class="u-handle">@${u.username}</div>
        </div>
        <button
          class="u-action"
          data-username="${u.username}"
          data-route="${actionRoute}"
          onclick="handleAction(this)"
        >${actionLabel}</button>
      </div>`;
  }).join('');
}


/* ── Action (follow / unfollow) ── */
function handleAction(btn) {
  const username = btn.dataset.username;
  const route    = btn.dataset.route;

  btn.disabled    = true;
  btn.textContent = '…';

  fetch(route, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ username }),
  })
    .then(r => r.json())
    .then(() => {
      const row = document.getElementById('row-' + username);
      if (row) row.classList.add('done');
      btn.textContent = 'Feito ✓';
    })
    .catch(() => {
      btn.disabled    = false;
      btn.textContent = 'Erro — tentar de novo';
    });
}


/* ── Bars ── */
function updateBar(barId, numId, value, max) {
  const bar = document.getElementById(barId);
  const num = document.getElementById(numId);
  if (bar) bar.style.width = (max > 0 ? (value / max) * 100 : 0) + '%';
  if (num) num.textContent = fmt(value);
}


/* ── Delta ── */
function updateDelta(elId, delta) {
  const el = document.getElementById(elId);
  if (!el || delta == null) return;
  el.textContent = (delta >= 0 ? '↑ +' : '↓ ') + delta + ' esta semana';
  el.className   = 'delta' + (delta < 0 ? ' neg' : '');
}


/* ── Render all data to DOM ── */
function renderData(data) {
  const name = data.full_name || data.username || '';
  setEl('avatar-initials', initials(name));
  setEl('profile-name',    name);
  setEl('profile-handle',  '@' + (data.username || ''));
  setEl('last-update',     'Última atualização: agora');

  setEl('stat-followers',    fmt(data.followers_count   || 0));
  setEl('stat-following',    fmt(data.following_count   || 0));
  setEl('stat-nonfollowers', fmt(data.not_following_back_count || 0));

  updateDelta('delta-followers', data.delta_followers);
  updateDelta('delta-following', data.delta_following);

  const youNotFB = data.you_not_following_back_count || 0;
  const max = Math.max(data.followers_count || 0, data.following_count || 0, 1);
  updateBar('bar-followers', 'barnum-followers', data.followers_count   || 0, max);
  updateBar('bar-following', 'barnum-following', data.following_count   || 0, max);
  updateBar('bar-nonfb',     'barnum-nonfb',     data.not_following_back_count || 0, max);
  updateBar('bar-younotfb',  'barnum-younotfb',  youNotFB, max);

  setEl('count-nonfb',    (data.not_following_back_count || 0) + ' pessoas');
  setEl('count-younotfb', (youNotFB || 0) + ' pessoas');

  renderList('list-nonfb',    data.not_following_back,     'Deixar de seguir', '/action/unfollow');
  renderList('list-younotfb', data.you_not_following_back, 'Seguir',           '/action/follow');
}


/* ══════════════════════════════════════════════════════
   LOAD DATA via SSE
══════════════════════════════════════════════════════ */

let activeEventSource = null;

function loadData() {
  const btn = document.getElementById('btn-refresh');
  if (btn) { btn.classList.add('loading'); btn.disabled = true; }

  // Fecha conexão anterior se ainda aberta
  if (activeEventSource) {
    activeEventSource.close();
    activeEventSource = null;
  }

  showOverlay();

  const es = new EventSource('/api/stats/stream');
  activeEventSource = es;

  es.onmessage = function(e) {
    let msg;
    try { msg = JSON.parse(e.data); }
    catch { return; }

    // Erro retornado pelo servidor
    if (msg.error) {
      es.close();
      activeEventSource = null;
      hideOverlay();

      if (msg.error === 'login_required') {
        window.location.href = '/login';
        return;
      }

      setEl('last-update', 'Erro: ' + msg.error);
      if (btn) { btn.classList.remove('loading'); btn.disabled = false; }
      return;
    }

    // Atualiza barra
    updateOverlay(msg.pct, msg.msg);

    // Dados finais chegaram
    if (msg.data) {
      es.close();
      activeEventSource = null;

      setTimeout(() => {
        hideOverlay();
        renderData(msg.data);
        if (btn) { btn.classList.remove('loading'); btn.disabled = false; }
      }, 700);
    }
  };

  es.onerror = function() {
    es.close();
    activeEventSource = null;
    hideOverlay();
    setEl('last-update', 'Erro ao conectar. Tente novamente.');
    if (btn) { btn.classList.remove('loading'); btn.disabled = false; }
  };
}


/* ── Init ── */
loadData();