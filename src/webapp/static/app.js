async function api(path, options) {
  const res = await fetch(path, options);
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = { ok: false, error: { message: text } }; }
  if (!res.ok) {
    throw new Error(JSON.stringify(json));
  }
  return json;
}

function getProjectId() {
  return localStorage.getItem('doe_project_id');
}

function setProjectId(id) {
  localStorage.setItem('doe_project_id', id);
  refreshCurrentProjectId();
}

function refreshCurrentProjectId() {
  const el = document.getElementById('currentProjectId');
  if (!el) return;
  el.textContent = getProjectId() || '(없음)';
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = value;
}

function setImg(id, base64Png) {
  const el = document.getElementById(id);
  if (!el) return;
  if (!base64Png) {
    el.removeAttribute('src');
    el.classList.add('d-none');
    return;
  }
  el.classList.remove('d-none');
  el.src = `data:image/png;base64,${base64Png}`;
}

function clearEl(el) {
  if (!el) return;
  while (el.firstChild) el.removeChild(el.firstChild);
}

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined) continue;
    if (k === 'class') el.className = String(v);
    else if (k === 'style') el.setAttribute('style', String(v));
    else if (k.startsWith('data-')) el.setAttribute(k, String(v));
    else el[k] = v;
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined) continue;
    if (typeof c === 'string' || typeof c === 'number' || typeof c === 'boolean') {
      el.appendChild(document.createTextNode(String(c)));
    } else {
      el.appendChild(c);
    }
  }
  return el;
}

function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function isDf(v) {
  return isPlainObject(v) && v.__type__ === 'DataFrame' && Array.isArray(v.columns) && Array.isArray(v.data);
}

function isSeries(v) {
  return isPlainObject(v) && v.__type__ === 'Series' && Array.isArray(v.index);
}

function parseMaybeNumber(v) {
  if (typeof v === 'number') return v;
  if (typeof v !== 'string') return null;
  const s = v.trim();
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function formatCell(v) {
  if (v === null || v === undefined) return '';
  if (typeof v === 'number') {
    if (!Number.isFinite(v)) return String(v);
    const abs = Math.abs(v);
    if (abs > 0 && abs < 1e-4) return v.toExponential(3);
    return Number.isInteger(v) ? String(v) : v.toFixed(4).replace(/0+$/, '').replace(/\.$/, '');
  }
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (typeof v === 'string') return v;
  return JSON.stringify(v);
}

function findPColumn(columns) {
  const candidates = ['PR(>F)', 'p_value', 'p-value', 'pvalue', 'P>|t|', 'P>|z|'];
  for (const c of candidates) {
    if (columns.includes(c)) return c;
  }
  for (const c of columns) {
    const s = String(c).toLowerCase();
    if (s.includes('p') && s.includes('value')) return c;
  }
  return null;
}

function renderDataFrame(df, { maxRows = 50 } = {}) {
  const columns = df.columns || [];
  const index = df.index || [];
  const rows = Array.isArray(df.data) ? df.data : [];
  const pCol = findPColumn(columns);

  const table = h('table', { class: 'table table-sm table-striped align-middle mb-0' });
  const thead = h('thead', {}, h('tr', {}, h('th', {}, '항목'), ...columns.map(c => h('th', {}, String(c)))));
  const tbody = h('tbody');

  const shown = rows.slice(0, maxRows);
  shown.forEach((row, i) => {
    const label = index[i] ?? String(i + 1);
    const pRaw = pCol ? row?.[pCol] : null;
    const pVal = parseMaybeNumber(pRaw);

    const tr = h('tr');
    if (pVal !== null) {
      if (pVal < 0.05) tr.classList.add('table-success');
      else if (pVal < 0.1) tr.classList.add('table-warning');
    }

    tr.appendChild(h('th', { scope: 'row', class: 'text-nowrap' }, String(label)));
    for (const c of columns) {
      tr.appendChild(h('td', { class: 'text-nowrap' }, formatCell(row?.[c])));
    }
    tbody.appendChild(tr);
  });

  table.appendChild(thead);
  table.appendChild(tbody);

  const wrap = h('div', { class: 'table-responsive' }, table);
  if (rows.length > maxRows) {
    wrap.appendChild(h('div', { class: 'small text-muted mt-1' }, `표시는 상위 ${maxRows}개 행만 보여줍니다. (총 ${rows.length}행)`));
  }
  return wrap;
}

function renderSeries(s, { maxItems = 80 } = {}) {
  const idx = s.index || [];
  const data = s.data || {};
  const name = s.name ? String(s.name) : '값';

  const table = h('table', { class: 'table table-sm table-striped align-middle mb-0' });
  const thead = h('thead', {}, h('tr', {}, h('th', {}, '항목'), h('th', {}, name)));
  const tbody = h('tbody');
  const shown = idx.slice(0, maxItems);
  shown.forEach((k) => {
    tbody.appendChild(h('tr', {}, h('th', { scope: 'row', class: 'text-nowrap' }, String(k)), h('td', { class: 'text-nowrap' }, formatCell(data?.[k]))));
  });
  table.appendChild(thead);
  table.appendChild(tbody);

  const wrap = h('div', { class: 'table-responsive' }, table);
  if (idx.length > maxItems) {
    wrap.appendChild(h('div', { class: 'small text-muted mt-1' }, `표시는 상위 ${maxItems}개 항목만 보여줍니다. (총 ${idx.length}개)`));
  }
  return wrap;
}

function renderKeyValueTable(obj) {
  const dl = h('dl', { class: 'row mb-0' });
  for (const [k, v] of Object.entries(obj || {})) {
    dl.appendChild(h('dt', { class: 'col-sm-4 text-muted' }, String(k)));
    const dd = h('dd', { class: 'col-sm-8 mb-2' });
    dd.appendChild(renderAny(v, 1));
    dl.appendChild(dd);
  }
  return dl;
}

function renderAny(v, depth = 0) {
  if (v === null || v === undefined) return h('span', { class: 'text-muted' }, '(없음)');
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return h('span', {}, formatCell(v));

  if (isDf(v)) return renderDataFrame(v);
  if (isSeries(v)) return renderSeries(v);

  if (Array.isArray(v)) {
    if (v.length === 0) return h('span', { class: 'text-muted' }, '(비어있음)');
    if (v.every(isPlainObject)) {
      const keys = Array.from(new Set(v.flatMap(o => Object.keys(o || {})))).slice(0, 12);
      const table = h('table', { class: 'table table-sm table-striped align-middle mb-0' });
      const thead = h('thead', {}, h('tr', {}, ...keys.map(k => h('th', {}, String(k)))));
      const tbody = h('tbody');
      v.slice(0, 30).forEach((row) => {
        tbody.appendChild(h('tr', {}, ...keys.map(k => h('td', { class: 'text-nowrap' }, formatCell(row?.[k])))));
      });
      table.appendChild(thead);
      table.appendChild(tbody);
      const wrap = h('div', { class: 'table-responsive' }, table);
      if (v.length > 30) wrap.appendChild(h('div', { class: 'small text-muted mt-1' }, `표시는 상위 30개 행만 보여줍니다. (총 ${v.length}행)`));
      return wrap;
    }
    const ul = h('ul', { class: 'mb-0' });
    v.slice(0, 50).forEach((item) => ul.appendChild(h('li', {}, renderAny(item, depth + 1))));
    if (v.length > 50) ul.appendChild(h('li', { class: 'text-muted' }, `... (총 ${v.length}개)`));
    return ul;
  }

  if (isPlainObject(v)) {
    if (typeof v.description === 'string' && isPlainObject(v.results)) {
      const parts = [];
      parts.push(h('div', { class: 'mb-2' }, h('div', { class: 'fw-semibold' }, '설명'), h('div', {}, v.description)));

      const summaryBadges = [];
      const res = v.results || {};
      if (typeof res.adj_r_squared === 'number') {
        summaryBadges.push(h('span', { class: 'badge text-bg-primary me-1' }, `Adj R²=${formatCell(res.adj_r_squared)}`));
      }
      if (summaryBadges.length) {
        parts.push(h('div', { class: 'mb-2' }, ...summaryBadges));
      }

      const details = h('div', { class: 'mt-2' });
      for (const [k, vv] of Object.entries(res)) {
        const block = h('details', { class: 'mb-2', open: depth < 1 });
        block.appendChild(h('summary', { class: 'small fw-semibold' }, String(k)));
        block.appendChild(h('div', { class: 'mt-2' }, renderAny(vv, depth + 1)));
        details.appendChild(block);
      }
      parts.push(details);
      return h('div', {}, parts);
    }

    const keys = Object.keys(v);
    if (keys.length <= 12 && depth >= 1) return renderKeyValueTable(v);
    const wrap = h('div', {});
    for (const [k, vv] of Object.entries(v)) {
      const block = h('details', { class: 'mb-2', open: depth < 1 });
      block.appendChild(h('summary', { class: 'small fw-semibold' }, String(k)));
      block.appendChild(h('div', { class: 'mt-2' }, renderAny(vv, depth + 1)));
      wrap.appendChild(block);
    }
    return wrap;
  }

  return h('span', {}, String(v));
}

function renderApiResult(targetId, data, { rawId = null } = {}) {
  const out = document.getElementById(targetId);
  const raw = document.getElementById(rawId || `${targetId}Raw`);

  if (raw) {
    raw.textContent = data === undefined ? '' : JSON.stringify(data, null, 2);
  }

  if (!out) return;
  if (out.tagName === 'PRE') {
    out.textContent = data === undefined ? '' : JSON.stringify(data, null, 2);
    return;
  }

  clearEl(out);
  if (data === undefined || data === null || data === '') return;
  out.appendChild(renderAny(data, 0));
}

function renderMessage(targetId, message, { variant = 'secondary', rawId = null } = {}) {
  const out = document.getElementById(targetId);
  const raw = document.getElementById(rawId || `${targetId}Raw`);
  if (raw) raw.textContent = '';
  if (!out) return;

  if (out.tagName === 'PRE') {
    out.textContent = String(message || '');
    return;
  }

  clearEl(out);
  if (!message) return;
  out.appendChild(h('div', { class: `alert alert-${variant} py-2 px-3 mb-0` }, String(message)));
}

function setSelectOptions(selectEl, values, preferred) {
  if (!selectEl) return;
  selectEl.innerHTML = '';
  for (const v of values) {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    if (preferred && preferred === v) opt.selected = true;
    selectEl.appendChild(opt);
  }
}

function getSelectedMulti(selectEl) {
  if (!selectEl) return [];
  return Array.from(selectEl.selectedOptions).map(o => o.value);
}

function guessNumericColumns(summary) {
  const dtypes = summary?.dtypes || {};
  const cols = summary?.columns || [];
  const numeric = [];
  for (const c of cols) {
    const dt = String(dtypes[c] || '').toLowerCase();
    if (dt.includes('int') || dt.includes('float') || dt.includes('double')) numeric.push(c);
  }
  return numeric;
}

function initRunPage() {
  refreshCurrentProjectId();
  // 프로젝트 UI는 노출하지 않되, 내부적으로는 기존 API를 그대로 사용
  ensureProject(false).then(() => loadColumns()).catch(() => {});
}

let _lastRecommendations = null;

function applySuggestedSelection(suggested) {
  if (!suggested) return;
  const response = suggested.response;
  const factors = suggested.factors || [];

  const responseSel = document.getElementById('responseCol');
  const factorsSel = document.getElementById('factorCols');
  if (responseSel && response) {
    for (const opt of responseSel.options) {
      opt.selected = (opt.value === response);
    }
  }
  if (factorsSel) {
    const factorSet = new Set(factors);
    for (const opt of factorsSel.options) {
      opt.selected = factorSet.has(opt.value);
    }
  }
}

async function fetchRecommendations() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/recommendations/projects/${pid}`);
  _lastRecommendations = resp.data;
  renderRecommendations(resp.data);
  return resp.data;
}

function renderRecommendations(data) {
  const wrap = document.getElementById('recommendations');
  const hint = document.getElementById('recommendationsHint');
  const profileBody = document.getElementById('recommendationsProfile');
  const defaultsEl = document.getElementById('recommendationsDefault');
  if (!wrap) return;

  wrap.innerHTML = '';
  const recs = data?.recommended || [];
  if (hint) {
    if (recs.length === 0) {
      hint.textContent = '추천할 분석이 없습니다(데이터 타입/컬럼 구성을 확인하세요).';
    } else {
      hint.textContent = '데이터 패턴 기반 추천입니다. 필요하면 response/factors를 바꿔 실행하세요.';
    }
  }

  for (const r of recs) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-success';
    btn.textContent = r.label;
    btn.title = r.reason || '';
    btn.onclick = () => runRecommendation(r);
    wrap.appendChild(btn);
  }

  if (defaultsEl) {
    const d = data?.default || {};
    const resp = d.response || '(없음)';
    const facs = (d.factors || []).join(', ') || '(없음)';
    defaultsEl.textContent = `기본 추정: response=${resp} / factors=${facs}`;
  }

  if (profileBody) {
    profileBody.innerHTML = '';
    const rows = data?.column_profile || [];
    for (const row of rows) {
      const tr = document.createElement('tr');
      const role = [];
      if (row.is_response_candidate) role.push('response 후보');
      if (row.is_factor_candidate) role.push('factor 후보');
      if (role.length === 0) role.push('-');

      const levels = Array.isArray(row.levels_preview) ? row.levels_preview.join(', ') : '';

      tr.innerHTML = `
        <td>${row.name}</td>
        <td><code>${row.dtype}</code></td>
        <td>${row.unique_non_null}</td>
        <td>${row.missing}</td>
        <td>${role.join(' / ')}</td>
        <td class="text-muted small">${levels}</td>
      `;

      // 후보 컬럼은 강조
      if (row.is_response_candidate) {
        tr.classList.add('table-warning');
      }
      if (row.is_factor_candidate) {
        tr.classList.add('table-success');
      }
      profileBody.appendChild(tr);
    }
  }
}

async function runRecommendation(r) {
  try {
    if (r?.suggested) {
      applySuggestedSelection(r.suggested);
    }

    const action = r?.action;
    if (action === 'doe_workflow') {
      return runDoeWorkflow();
    }
    if (action === 'correlation') {
      await runCorrelation();
      return chartCorrelationMatrix();
    }
    if (action === 'regression') {
      return runRegression();
    }
    if (action === 'rsm') {
      return runRsmSelected();
    }
    if (action === 'chart_main_effects') {
      const { response, factors } = getResponseAndFactors();
      if (!response || factors.length < 1) return;
      return createChartWith({ chart_type: 'main_effects', x_var: factors[0], y_var: response, imgId: 'imgMainEffects' });
    }
    if (action === 'chart_interaction') {
      const { response, factors } = getResponseAndFactors();
      if (!response || factors.length < 2) return;
      return createChartWith({ chart_type: 'interaction', x_var: factors[0], group_var: factors[1], y_var: response, imgId: 'imgInteraction' });
    }
  } catch (e) {
    renderMessage('analysisOut', String(e), { variant: 'danger' });
  }
}

async function runRecommendedFirst() {
  const data = _lastRecommendations || await fetchRecommendations();
  const first = (data?.recommended || [])[0];
  if (!first) {
    renderMessage('analysisOut', '추천 항목이 없습니다.', { variant: 'warning' });
    return;
  }
  return runRecommendation(first);
}

async function resetWorkflow() {
  try {
    await ensureProject(true);
    renderMessage('dataOut', '새 작업을 시작했습니다. 데이터를 업로드하세요.');
    renderApiResult('analysisOut', null);
    renderApiResult('chartOut', null);
    setImg('imgMainEffects', null);
    setImg('imgInteraction', null);
    setImg('imgOther', null);
    const responseSel = document.getElementById('responseCol');
    const factorsSel = document.getElementById('factorCols');
    if (responseSel) responseSel.innerHTML = '';
    if (factorsSel) factorsSel.innerHTML = '';
  } catch (e) {
    renderMessage('dataOut', String(e), { variant: 'danger' });
  }
}

async function ensureProject(forceNew=false) {
  if (!forceNew && getProjectId()) return getProjectId();
  const resp = await api('/api/v1/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: null })
  });
  setProjectId(resp.data.project_id);
  return resp.data.project_id;
}

async function createProject() {
  const name = document.getElementById('projectName')?.value || null;
  const resp = await api('/api/v1/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  });
  setProjectId(resp.data.project_id);
  renderApiResult('projectOut', resp.data);
}

async function loadProjectInfo() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}`);
  renderApiResult('projectOut', resp.data);
}

async function importProject() {
  const file = document.getElementById('importFile').files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const resp = await api('/api/v1/projects/import', { method: 'POST', body: fd });
  setProjectId(resp.data.project_id);
  renderApiResult('projectOut', resp.data);
}

async function exportProject() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/export`);
  // content는 (이미 pretty된) JSON 문자열
  try {
    renderApiResult('projectOut', JSON.parse(resp.data.content));
  } catch {
    renderMessage('projectOut', resp.data.content);
  }
}

async function uploadData() {
  const pid = await ensureProject(false);
  const file = document.getElementById('dataFile').files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const resp = await api(`/api/v1/projects/${pid}/data/upload`, { method: 'POST', body: fd });
  renderApiResult('dataOut', resp.data);
}

async function uploadDataAndLoadColumns() {
  try {
    await uploadData();
    await loadColumns();
  } catch (e) {
    renderMessage('dataOut', String(e), { variant: 'danger' });
  }
}

async function loadColumns() {
  const pid = await ensureProject(false);
  try {
    const resp = await api(`/api/v1/projects/${pid}/data/summary`);
    const summary = resp.data;
    const cols = summary.columns || [];
    const numeric = guessNumericColumns(summary);

    const responseSel = document.getElementById('responseCol');
    const factorsSel = document.getElementById('factorCols');

    const defaultResponse = numeric[0] || cols[0] || '';
    setSelectOptions(responseSel, cols, defaultResponse);
    setSelectOptions(factorsSel, cols.filter(c => c !== defaultResponse));

    // 기본으로 앞의 몇 개 요인을 선택해두기
    if (factorsSel) {
      const maxSelect = Math.min(3, factorsSel.options.length);
      for (let i = 0; i < maxSelect; i++) {
        factorsSel.options[i].selected = true;
      }
    }

    renderApiResult('dataOut', summary);
    await fetchRecommendations();
  } catch (e) {
    // 데이터 업로드 전일 수 있음
    renderMessage('dataOut', '데이터를 먼저 업로드하세요.', { variant: 'warning' });
    const wrap = document.getElementById('recommendations');
    const hint = document.getElementById('recommendationsHint');
    if (wrap) wrap.innerHTML = '';
    if (hint) hint.textContent = '';
  }
}

async function fetchDataSummary() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/data/summary`);
  renderApiResult('dataOut', resp.data);
}

async function fetchDataPreview() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/data/preview?rows=20`);
  renderApiResult('dataOut', resp.data);
}

function parseCsvInts(s) {
  return s.split(',').map(x => parseInt(x.trim(), 10)).filter(x => !Number.isNaN(x));
}
function parseCsvStrs(s) {
  return s.split(',').map(x => x.trim()).filter(x => x.length > 0);
}

async function designFullFactorial() {
  const levels = parseCsvInts(document.getElementById('ffLevels').value);
  const resp = await api('/api/v1/design/full_factorial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ levels })
  });
  renderApiResult('designOut', resp.data);
}

async function designFractional() {
  const design_str = document.getElementById('fracStr').value;
  const resp = await api('/api/v1/design/fractional_factorial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ design_str })
  });
  renderApiResult('designOut', resp.data);
}

async function designPB() {
  const factors = parseInt(document.getElementById('pbFactors').value, 10);
  const resp = await api('/api/v1/design/plackett_burman', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ factors })
  });
  renderApiResult('designOut', resp.data);
}

async function designOA() {
  const factors = parseInt(document.getElementById('oaFactors').value, 10);
  const design = document.getElementById('oaDesign').value;
  const resp = await api('/api/v1/design/orthogonal_array', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ factors, design })
  });
  renderApiResult('designOut', resp.data);
}

async function runAnalysis(kind) {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/analysis/projects/${pid}/${kind}`, { method: 'POST' });
  renderApiResult('analysisOut', resp.data);
}

async function runBasicStats() { return runAnalysis('basic_statistics'); }
async function runCorrelation() { return runAnalysis('correlation'); }
async function runAnova() { return runAnalysis('anova'); }
async function runRegression() { return runAnalysis('regression'); }

function getResponseAndFactors() {
  const response = document.getElementById('responseCol')?.value;
  const factors = getSelectedMulti(document.getElementById('factorCols'));
  return { response, factors };
}

async function runMainEffectsAnovaSelected() {
  const pid = await ensureProject(false);
  const { response, factors } = getResponseAndFactors();
  const resp = await api(`/api/v1/analysis/projects/${pid}/main_effects_anova`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response, factors, analysis_type: '부분요인 ANOVA' })
  });
  renderApiResult('analysisOut', resp.data);
}

async function runRsmSelected() {
  const pid = await ensureProject(false);
  const { response, factors } = getResponseAndFactors();
  const resp = await api(`/api/v1/analysis/projects/${pid}/rsm_quadratic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response, factors, analysis_type: 'RSM' })
  });
  renderApiResult('analysisOut', resp.data);
}

// 레거시 페이지 호환: responseCol이 있으면 선택 기반을 사용
async function runRsm() {
  if (document.getElementById('responseCol')) {
    return runRsmSelected();
  }
  const pid = await ensureProject(false);
  const response = document.getElementById('rsmResp')?.value;
  const factorsRaw = document.getElementById('rsmFactors')?.value;
  const factors = factorsRaw ? parseCsvStrs(factorsRaw) : [];
  const resp = await api(`/api/v1/analysis/projects/${pid}/rsm_quadratic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response, factors, analysis_type: 'RSM' })
  });
  renderApiResult('analysisOut', resp.data);
}

async function createChartWith({ chart_type, x_var=null, y_var=null, group_var=null, imgId='imgOther' }) {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/charts/projects/${pid}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_type, x_var, y_var, group_var, options: null })
  });
  setImg(imgId, resp.data.image_base64_png);
  renderApiResult('chartOut', resp.data);
  return resp.data;
}

async function chartCorrelationMatrix() {
  try {
    await createChartWith({ chart_type: 'correlation_matrix', imgId: 'imgOther' });
  } catch (e) {
    renderMessage('chartOut', String(e), { variant: 'danger' });
  }
}

async function chartHistogramResponse() {
  const response = document.getElementById('responseCol')?.value;
  if (!response) return;
  try {
    await createChartWith({ chart_type: 'histogram', x_var: response, imgId: 'imgOther' });
  } catch (e) {
    renderMessage('chartOut', String(e), { variant: 'danger' });
  }
}

async function runDoeWorkflow() {
  const pid = await ensureProject(false);
  const { response, factors } = getResponseAndFactors();
  if (!response || factors.length === 0) {
    renderMessage('analysisOut', 'response와 factors를 선택하세요.', { variant: 'warning' });
    return;
  }
  try {
    const res = await api(`/api/v1/analysis/projects/${pid}/doe_anova`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response, factors })
    });
    renderApiResult('analysisOut', res.data);

    // 시각화(가능한 경우): 주효과도/상호작용도
    setImg('imgMainEffects', null);
    setImg('imgInteraction', null);

    await createChartWith({
      chart_type: 'main_effects',
      x_var: factors[0],
      y_var: response,
      imgId: 'imgMainEffects'
    });

    if (factors.length >= 2) {
      await createChartWith({
        chart_type: 'interaction',
        x_var: factors[0],
        group_var: factors[1],
        y_var: response,
        imgId: 'imgInteraction'
      });
    }
  } catch (e) {
    renderMessage('analysisOut', String(e), { variant: 'danger' });
  }
}

async function runDoeAnova() {
  const pid = await ensureProject(false);
  const response = document.getElementById('doeResp').value;
  const factors = parseCsvStrs(document.getElementById('doeFactors').value);
  const resp = await api(`/api/v1/analysis/projects/${pid}/doe_anova`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response, factors })
  });
  renderApiResult('analysisOut', resp.data);
}

async function createChart() {
  const pid = await ensureProject(false);
  const chart_type = document.getElementById('chartType').value;
  const x_var = document.getElementById('chartX').value || null;
  const y_var = document.getElementById('chartY').value || null;
  const group_var = document.getElementById('chartGroup').value || null;
  const resp = await api(`/api/v1/charts/projects/${pid}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_type, x_var, y_var, group_var, options: null })
  });
  const img = document.getElementById('chartImg');
  if (img) {
    img.classList.remove('d-none');
    img.src = `data:image/png;base64,${resp.data.image_base64_png}`;
  }
  renderApiResult('chartOut', resp.data);
}

async function loadAnalysisHistory() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/analysis/projects/${pid}/history`);
  renderApiResult('historyOut', resp.data);
}

async function loadChartHistory() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/charts/projects/${pid}/history`);
  renderApiResult('historyOut', resp.data);
}
