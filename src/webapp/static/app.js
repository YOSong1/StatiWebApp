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
    return;
  }
  el.src = `data:image/png;base64,${base64Png}`;
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
      return createChartWith({ chart_type: '주효과도', x_var: factors[0], y_var: response, imgId: 'imgMainEffects' });
    }
    if (action === 'chart_interaction') {
      const { response, factors } = getResponseAndFactors();
      if (!response || factors.length < 2) return;
      return createChartWith({ chart_type: '상호작용도', x_var: factors[0], group_var: factors[1], y_var: response, imgId: 'imgInteraction' });
    }
  } catch (e) {
    setText('analysisOut', String(e));
  }
}

async function runRecommendedFirst() {
  const data = _lastRecommendations || await fetchRecommendations();
  const first = (data?.recommended || [])[0];
  if (!first) {
    setText('analysisOut', '추천 항목이 없습니다.');
    return;
  }
  return runRecommendation(first);
}

async function resetWorkflow() {
  try {
    await ensureProject(true);
    setText('dataOut', '새 작업을 시작했습니다. 데이터를 업로드하세요.');
    setText('analysisOut', '');
    setText('chartOut', '');
    setImg('imgMainEffects', null);
    setImg('imgInteraction', null);
    setImg('imgOther', null);
    const responseSel = document.getElementById('responseCol');
    const factorsSel = document.getElementById('factorCols');
    if (responseSel) responseSel.innerHTML = '';
    if (factorsSel) factorsSel.innerHTML = '';
  } catch (e) {
    setText('dataOut', String(e));
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
  document.getElementById('projectOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function loadProjectInfo() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}`);
  document.getElementById('projectOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function importProject() {
  const file = document.getElementById('importFile').files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const resp = await api('/api/v1/projects/import', { method: 'POST', body: fd });
  setProjectId(resp.data.project_id);
  document.getElementById('projectOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function exportProject() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/export`);
  document.getElementById('projectOut').textContent = resp.data.content;
}

async function uploadData() {
  const pid = await ensureProject(false);
  const file = document.getElementById('dataFile').files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const resp = await api(`/api/v1/projects/${pid}/data/upload`, { method: 'POST', body: fd });
  setText('dataOut', JSON.stringify(resp.data, null, 2));
}

async function uploadDataAndLoadColumns() {
  try {
    await uploadData();
    await loadColumns();
  } catch (e) {
    setText('dataOut', String(e));
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

    setText('dataOut', JSON.stringify(summary, null, 2));
    await fetchRecommendations();
  } catch (e) {
    // 데이터 업로드 전일 수 있음
    setText('dataOut', '데이터를 먼저 업로드하세요.');
    const wrap = document.getElementById('recommendations');
    const hint = document.getElementById('recommendationsHint');
    if (wrap) wrap.innerHTML = '';
    if (hint) hint.textContent = '';
  }
}

async function fetchDataSummary() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/data/summary`);
  document.getElementById('dataOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function fetchDataPreview() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/projects/${pid}/data/preview?rows=20`);
  document.getElementById('dataOut').textContent = JSON.stringify(resp.data, null, 2);
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
  document.getElementById('designOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function designFractional() {
  const design_str = document.getElementById('fracStr').value;
  const resp = await api('/api/v1/design/fractional_factorial', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ design_str })
  });
  document.getElementById('designOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function designPB() {
  const factors = parseInt(document.getElementById('pbFactors').value, 10);
  const resp = await api('/api/v1/design/plackett_burman', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ factors })
  });
  document.getElementById('designOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function designOA() {
  const factors = parseInt(document.getElementById('oaFactors').value, 10);
  const design = document.getElementById('oaDesign').value;
  const resp = await api('/api/v1/design/orthogonal_array', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ factors, design })
  });
  document.getElementById('designOut').textContent = JSON.stringify(resp.data, null, 2);
}

async function runAnalysis(kind) {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/analysis/projects/${pid}/${kind}`, { method: 'POST' });
  setText('analysisOut', JSON.stringify(resp.data, null, 2));
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
  setText('analysisOut', JSON.stringify(resp.data, null, 2));
}

async function runRsmSelected() {
  const pid = await ensureProject(false);
  const { response, factors } = getResponseAndFactors();
  const resp = await api(`/api/v1/analysis/projects/${pid}/rsm_quadratic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response, factors, analysis_type: 'RSM' })
  });
  setText('analysisOut', JSON.stringify(resp.data, null, 2));
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
  setText('analysisOut', JSON.stringify(resp.data, null, 2));
}

async function createChartWith({ chart_type, x_var=null, y_var=null, group_var=null, imgId='imgOther' }) {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/charts/projects/${pid}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_type, x_var, y_var, group_var, options: null })
  });
  setImg(imgId, resp.data.image_base64_png);
  setText('chartOut', JSON.stringify(resp.data, null, 2));
  return resp.data;
}

async function chartCorrelationMatrix() {
  try {
    await createChartWith({ chart_type: '상관행렬', imgId: 'imgOther' });
  } catch (e) {
    setText('chartOut', String(e));
  }
}

async function chartHistogramResponse() {
  const response = document.getElementById('responseCol')?.value;
  if (!response) return;
  try {
    await createChartWith({ chart_type: '히스토그램', x_var: response, imgId: 'imgOther' });
  } catch (e) {
    setText('chartOut', String(e));
  }
}

async function runDoeWorkflow() {
  const pid = await ensureProject(false);
  const { response, factors } = getResponseAndFactors();
  if (!response || factors.length === 0) {
    setText('analysisOut', 'response와 factors를 선택하세요.');
    return;
  }
  try {
    const res = await api(`/api/v1/analysis/projects/${pid}/doe_anova`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ response, factors })
    });
    setText('analysisOut', JSON.stringify(res.data, null, 2));

    // 시각화(가능한 경우): 주효과도/상호작용도
    setImg('imgMainEffects', null);
    setImg('imgInteraction', null);

    await createChartWith({
      chart_type: '주효과도',
      x_var: factors[0],
      y_var: response,
      imgId: 'imgMainEffects'
    });

    if (factors.length >= 2) {
      await createChartWith({
        chart_type: '상호작용도',
        x_var: factors[0],
        group_var: factors[1],
        y_var: response,
        imgId: 'imgInteraction'
      });
    }
  } catch (e) {
    setText('analysisOut', String(e));
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
  setText('analysisOut', JSON.stringify(resp.data, null, 2));
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
  img.src = `data:image/png;base64,${resp.data.image_base64_png}`;
  setText('chartOut', JSON.stringify(resp.data, null, 2));
}

async function loadAnalysisHistory() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/analysis/projects/${pid}/history`);
  setText('historyOut', JSON.stringify(resp.data, null, 2));
}

async function loadChartHistory() {
  const pid = await ensureProject(false);
  const resp = await api(`/api/v1/charts/projects/${pid}/history`);
  setText('historyOut', JSON.stringify(resp.data, null, 2));
}
