'use strict';
/* 魔術方塊速解教練 — UI / 3D / 教學流程 */
(function () {
  const E = window.RCube, S = window.RCSolver;
  const $ = (id) => document.getElementById(id);

  // ---------- 常數 ----------
  const COLORS = ['W', 'Y', 'R', 'O', 'G', 'B'];
  const FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B'];         // = 引擎 facelet 順序
  // 展開圖預設（與教學一致：黃上、白下、綠前、紅右、藍後、橘左）
  const DEFAULT_CENTER = { U: 'Y', R: 'R', F: 'G', D: 'W', L: 'O', B: 'B' };
  // 每個面在 12x9 網格中的位置 [colStart,rowStart]
  const NET_POS = { U: [3, 0], L: [0, 3], F: [3, 3], R: [6, 3], B: [9, 3], D: [3, 6] };
  const FACE_CN = { U: '上面 (U)', R: '右面 (R)', F: '前面 (F)', D: '下面 (D)', L: '左面 (L)', B: '後面 (B)' };
  const FACE_TURN_CN = { U: '上層', D: '下層', R: '右層', L: '左層', F: '前層', B: '後層' };

  // 目前輸入狀態：每面 9 格顏色
  const net = {};
  FACE_ORDER.forEach((f) => { net[f] = Array(9).fill(DEFAULT_CENTER[f]); });
  let selColor = 'W';
  let mode = 'cfop';

  // ---------- 建立展開圖 ----------
  const netEl = $('net');
  function buildNet() {
    netEl.innerHTML = '';
    for (const f of ['U', 'L', 'F', 'R', 'B', 'D']) {
      const [cs, rs] = NET_POS[f];
      const face = document.createElement('div');
      face.className = 'face';
      face.style.gridColumn = `${cs + 1} / span 3`;
      face.style.gridRow = `${rs + 1} / span 3`;
      for (let i = 0; i < 9; i++) {
        const cell = document.createElement('div');
        cell.className = 'cell' + (i === 4 ? ' center' : '');
        cell.dataset.c = net[f][i];
        cell.dataset.face = f; cell.dataset.i = i;
        face.appendChild(cell);
      }
      netEl.appendChild(face);
    }
  }
  netEl.addEventListener('click', (e) => {
    const cell = e.target.closest('.cell');
    if (!cell) return;
    const f = cell.dataset.face, i = +cell.dataset.i;
    net[f][i] = selColor;
    cell.dataset.c = selColor;
    setMsg('', '');
  });
  // 調色盤
  $('palette').addEventListener('click', (e) => {
    const sw = e.target.closest('.sw'); if (!sw) return;
    selColor = sw.dataset.c;
    document.querySelectorAll('.sw').forEach((s) => s.classList.toggle('sel', s === sw));
  });
  // 教學模式切換
  document.querySelector('.modebar').addEventListener('click', (e) => {
    const b = e.target.closest('.modebtn'); if (!b) return;
    mode = b.dataset.mode;
    document.querySelectorAll('.modebtn').forEach((x) => x.classList.toggle('active', x === b));
  });

  function faceletsFromNet() {
    let s = '';
    for (const f of FACE_ORDER) s += net[f].join('');
    return s;
  }
  function loadFacelets(str) {
    let k = 0;
    for (const f of FACE_ORDER) for (let i = 0; i < 9; i++) net[f][i] = str[k++];
    buildNet();
  }

  // ---------- 驗證 ----------
  const CENTER_ROLE = { 4: 'Y', 13: 'R', 22: 'G', 31: 'W', 40: 'O', 49: 'B' }; // facelet 中心→角色色
  const SOLVED_PIECE_KEYS = (() => {
    const set = new Set();
    for (const cu of E.solvedCube()) set.add(cu.stickers.map((s) => s.c).sort().join(''));
    return set;
  })();
  function validate(fac) {
    // 1) 顏色數量
    const cnt = {}; for (const c of fac) cnt[c] = (cnt[c] || 0) + 1;
    for (const c of COLORS) if (cnt[c] !== 9)
      return { ok: false, msg: `顏色數量不對：${cnName(c)} 有 ${cnt[c] || 0} 個（應該是 9 個）。請檢查每個顏色都剛好 9 格。` };
    // 2) 中心不重複
    const centers = [4, 13, 22, 31, 40, 49].map((i) => fac[i]);
    if (new Set(centers).size !== 6)
      return { ok: false, msg: '六個中心塊的顏色必須都不一樣，請檢查中心格。' };
    // 3) 建立角色對照並檢查每個塊合法
    const M = {}; for (const i in CENTER_ROLE) M[fac[+i]] = CENTER_ROLE[i];
    const roleStr = [...fac].map((c) => M[c]).join('');
    const model = E.fromFacelets(roleStr);
    const seen = {};
    for (const cu of model) {
      const key = cu.stickers.map((s) => s.c).sort().join('');
      if (!SOLVED_PIECE_KEYS.has(key))
        return { ok: false, msg: '有一個角/邊塊的配色不可能出現（例如同一塊出現對面顏色）。請再對照一次方塊。' };
      seen[key] = (seen[key] || 0) + 1;
    }
    for (const k in seen) if (seen[k] > 1)
      return { ok: false, msg: '有重複的角/邊塊，代表某些格子顏色貼錯了，請再檢查一次。' };
    return { ok: true, roleStr, userFac: fac };
  }
  function cnName(c) { return { W: '白', Y: '黃', R: '紅', O: '橘', G: '綠', B: '藍' }[c]; }

  function setMsg(t, cls) { const m = $('msg'); m.textContent = t; m.className = cls || ''; }

  // ---------- 求解流程資料 ----------
  let STEPS = [];      // 展平後的每一步 {stageId,stageTitle,face,quarter,notation,say}
  let STAGE_LIST = []; // 章節 {id,title,count}
  let inputRoleStr = null, inputUserStr = null;

  // CFOP 四大階段的號碼與說明
  const STAGE_STEP = {
    cross: '第 1 步 · Cross', f2l: '第 2 步 · F2L', oll: '第 3 步 · OLL', pll: '第 4 步 · PLL',
    ll1: '第 3 步 · OLL', ll2: '第 3 步 · OLL', ll3: '第 4 步 · PLL', ll4: '第 4 步 · PLL',
  };

  // 各種轉法的中文說明
  const TURN_CN = {
    U: '上層', D: '下層', R: '右層', L: '左層', F: '前層', B: '後層',
    M: '中間直排(跟左層方向)', E: '中間橫排(跟下層方向)', S: '中間直排(跟前層方向)',
    r: '右邊兩層', l: '左邊兩層', u: '上面兩層', d: '下面兩層', f: '前面兩層', b: '後面兩層',
    x: '整顆(跟右層方向翻)', y: '整顆(跟上層方向轉)', z: '整顆(跟前層方向轉)',
  };
  function notationOf(token, q) {
    // 顯示：寬轉用小寫、旋轉用小寫；prime/2
    const suf = q === 1 ? '' : q === 2 ? '2' : "'";
    return token + suf;
  }
  function sayOf(token, q) {
    const name = TURN_CN[token] || token;
    const dir = q === 1 ? '順時針 90°' : q === 3 ? '逆時針 90°' : '180°';
    if ('xyz'.includes(token)) return `把整顆方塊 ${name.replace('整顆','').replace(/[()]/g,'')} 轉 ${dir}`;
    return `把「${name}」轉 ${dir}`;
  }

  function buildSteps(stages) {
    STEPS = []; STAGE_LIST = [];
    let f2lCount = 0;
    for (const st of stages) {
      let title = st.title;
      if (st.id === 'f2l') { f2lCount++; }
      const stepTag = STAGE_STEP[st.id] || '';
      STAGE_LIST.push({ id: st.id, title, count: st.moves.length });
      for (const m of st.moves) {
        const token = m.move || m.face;
        STEPS.push({
          stageId: st.id, stageTitle: title, stepTag, desc: st.desc,
          token, quarter: m.quarter,
          notation: notationOf(token, m.quarter), say: sayOf(token, m.quarter),
        });
      }
    }
  }

  // ---------- 3D 立方體 ----------
  const S3 = 62, OFF = 31, STK = 56;                 // 尺寸
  const cubeEl = $('cube');
  const DIR_FACE = [                                  // dir → CSS transform
    { d: [0, 1, 0], t: `rotateX(90deg) translateZ(${OFF}px)` },   // +y 上
    { d: [0, -1, 0], t: `rotateX(-90deg) translateZ(${OFF}px)` }, // -y 下
    { d: [1, 0, 0], t: `rotateY(90deg) translateZ(${OFF}px)` },   // +x 右
    { d: [-1, 0, 0], t: `rotateY(-90deg) translateZ(${OFF}px)` }, // -x 左
    { d: [0, 0, 1], t: `translateZ(${OFF}px)` },                  // +z 前
    { d: [0, 0, -1], t: `rotateY(180deg) translateZ(${OFF}px)` }, // -z 後
  ];
  function transformFor(dir) {
    for (const f of DIR_FACE) if (f.d[0] === dir[0] && f.d[1] === dir[1] && f.d[2] === dir[2]) return f.t;
    return '';
  }
  let liveModel = null;

  function cubieKey(cu) { return cu.stickers.map((s) => s.c).sort().join('') + '|' + cu.stickers.length; }
  function renderCube(model) {
    cubeEl.innerHTML = '';
    for (const cu of model) {
      const el = document.createElement('div');
      el.className = 'cubie';
      el.dataset.key = cu.pos.join(','); // 以「位置」為 key（渲染用）
      el.style.transform = `translate3d(${cu.pos[0] * S3}px, ${-cu.pos[1] * S3}px, ${cu.pos[2] * S3}px)`;
      for (const s of cu.stickers) {
        const st = document.createElement('div');
        st.className = 'stk'; st.dataset.c = s.c;
        st.style.width = st.style.height = STK + 'px';
        st.style.left = st.style.top = '0';
        st.style.margin = (-STK / 2) + 'px';
        st.style.transform = transformFor(s.dir);
        el.appendChild(st);
      }
      cubeEl.appendChild(el);
    }
  }

  // 動畫轉一層／多層／整顆：move={token,quarter}
  function animateMove(model, move, ms) {
    const token = move.token || move.move || move.face;
    const spec = E.MOVE_SPEC[token];
    if (!spec) { E.applyMove(model, token, move.quarter); renderCube(model); return; }
    const idx = spec.axis === 'x' ? 0 : spec.axis === 'y' ? 1 : 2;
    const pivot = document.createElement('div');
    pivot.className = 'pivot';
    cubeEl.appendChild(pivot);
    for (const el of Array.from(cubeEl.children)) {
      if (el === pivot) continue;
      const pos = el.dataset.key.split(',').map(Number);
      if (spec.layers.indexOf(pos[idx]) !== -1) pivot.appendChild(el);
    }
    // 旋轉角度：用「最短」等效轉法（' 走 -90 而非 +270）
    const qturns = move.quarter === 3 ? -1 : move.quarter;
    const modelDeg = spec.rd * 90 * qturns;
    const axisVec = spec.axis === 'x' ? '1,0,0' : spec.axis === 'y' ? '0,1,0' : '0,0,1';
    const deg = -modelDeg; // 位置把模型 +y 對到螢幕上方，旋轉角需取反
    pivot.style.transition = 'none';
    pivot.style.transform = 'rotate3d(0,0,1,0deg)';
    requestAnimationFrame(() => {
      pivot.style.transition = `transform ${ms}ms ease-in-out`;
      pivot.style.transform = `rotate3d(${axisVec},${deg}deg)`;
    });
    setTimeout(() => { E.applyMove(model, token, move.quarter); renderCube(model); }, ms + 20);
  }

  // ---------- 播放控制 ----------
  let cur = -1;            // 目前已完成到第幾步（-1 = 尚未開始，顯示打亂原狀）
  let playing = false, playTimer = null, animating = false;

  function modelAtStart() { return E.fromFacelets(inputUserStr); }
  function rebuildTo(n) {  // 直接重算到第 n 步（不動畫）
    const m = modelAtStart();
    for (let i = 0; i < n; i++) E.applyMove(m, STEPS[i].token, STEPS[i].quarter);
    return m;
  }
  function speedMs() { const v = +$('speed').value; return Math.round(560 - v * 46); }

  function updateInfo() {
    const total = STEPS.length;
    if (cur < 0) {
      $('siStage').textContent = '準備開始';
      $('siNotation').textContent = '–';
      $('siSay').textContent = '這是你打亂的樣子。按「下一步 ▶」或「播放」開始還原。';
      $('siProg').textContent = `共 ${total} 步`;
    } else if (cur >= total) {
      $('siStage').textContent = '🎉 完成！';
      $('siNotation').textContent = '✓';
      $('siSay').textContent = '恭喜，方塊已經還原！可以按 ⏮ 再看一次。';
      $('siProg').textContent = `${total} / ${total}`;
    } else {
      const s = STEPS[cur];
      $('siStage').textContent = (s.stepTag ? s.stepTag + '　' : '') + s.stageTitle;
      $('siNotation').textContent = s.notation;
      $('siSay').textContent = s.say + (s.desc ? '　—　' + s.desc : '');
      $('siProg').textContent = `第 ${cur + 1} / ${total} 步`;
    }
    // 情況小圖示（只在頂層各階段顯示）
    const sidx = curStageIndex();
    const dg = (cur >= 0 && cur < total && sidx >= 0 && sidx < STAGE_LIST.length) ? STAGE_LIST[sidx].diagram : '';
    $('caseDiagram').innerHTML = dg || '';
    // 章節 chips
    const list = $('stagesList'); list.innerHTML = '';
    let acc = 0; const idxStage = curStageIndex();
    STAGE_LIST.forEach((st, i) => {
      const chip = document.createElement('span');
      chip.className = 'chip' + (i < idxStage ? ' done' : i === idxStage ? ' cur' : '');
      chip.textContent = st.title;
      list.appendChild(chip);
      acc += st.count;
    });
    $('cPrev').disabled = cur < 0 || animating;
    $('cFirst').disabled = cur < 0 || animating;
    $('cNext').disabled = cur >= total || animating;
    $('cLast').disabled = cur >= total || animating;
  }
  function curStageIndex() {
    if (cur < 0) return -1;
    if (cur >= STEPS.length) return STAGE_LIST.length;
    let acc = 0;
    for (let i = 0; i < STAGE_LIST.length; i++) { acc += STAGE_LIST[i].count; if (cur < acc) return i; }
    return STAGE_LIST.length - 1;
  }

  function doNext(animate) {
    const nextIdx = cur + 1;
    if (animating || nextIdx >= STEPS.length + 0 && cur >= STEPS.length) { stopPlay(); return; }
    const mv = STEPS[nextIdx];
    if (!mv) { cur = STEPS.length; updateInfo(); stopPlay(); return; }
    cur = nextIdx;
    if (animate) {
      animating = true; updateInfo();
      animateMove(liveModel, mv, speedMs());
      setTimeout(() => { animating = false; afterStep(); }, speedMs() + 40);
    } else {
      E.applyMove(liveModel, mv.token, mv.quarter); renderCube(liveModel); afterStep();
    }
  }
  function afterStep() {
    updateInfo();
    if (playing) {
      if (cur >= STEPS.length) stopPlay();
      else playTimer = setTimeout(() => doNext(true), 150);
    }
  }
  function doPrev() {
    if (animating || cur < 0) return;
    cur -= 1;                       // cur 表示「已完成到第幾步（0-based）」
    liveModel = rebuildTo(cur + 1); // 重算到該狀態
    renderCube(liveModel); updateInfo();
  }
  function goFirst() { stopPlay(); cur = -1; liveModel = modelAtStart(); renderCube(liveModel); updateInfo(); }
  function goLast() {
    stopPlay(); cur = STEPS.length; liveModel = rebuildTo(STEPS.length); renderCube(liveModel); updateInfo();
  }
  function togglePlay() {
    if (playing) { stopPlay(); return; }
    if (cur >= STEPS.length) goFirst();
    playing = true; $('cPlay').textContent = '❚❚ 暫停'; doNext(true);
  }
  function stopPlay() { playing = false; clearTimeout(playTimer); $('cPlay').textContent = '▶ 播放'; updateInfo(); }

  // ---------- 事件 ----------
  $('cNext').onclick = () => { stopPlay(); doNext(true); };
  $('cPrev').onclick = () => { stopPlay(); doPrev(); };
  $('cFirst').onclick = goFirst;
  $('cLast').onclick = goLast;
  $('cPlay').onclick = togglePlay;

  $('btnDemo').onclick = () => {
    const scr = randomScramble(22);
    const m = E.solvedCube();
    // 用「使用者色」呈現：預設方案套用後打亂
    const solvedUser = solvedUserFacelets();
    const um = E.fromFacelets(solvedUser);
    E.applyMoves(um, scr);
    loadFacelets(E.toFacelets(um));
    setMsg('已填入一組隨機打亂，按「驗證並產生解法」試試看。', 'ok');
  };
  $('btnReset').onclick = () => {
    FACE_ORDER.forEach((f) => { net[f] = Array(9).fill(DEFAULT_CENTER[f]); });
    buildNet(); setMsg('已回到完成狀態。', '');
  };
  $('btnSolve').onclick = solveNow;
  $('btnBack').onclick = () => switchTab('input');
  $('tabInput').onclick = () => switchTab('input');
  $('tabSolve').onclick = () => { if (!$('tabSolve').disabled) switchTab('solve'); };

  function solvedUserFacelets() {
    // 以預設中心色排出「完成」的使用者色字串
    let s = '';
    for (const f of FACE_ORDER) s += DEFAULT_CENTER[f].repeat(9);
    return s;
  }
  function randomScramble(n) {
    const faces = ['U', 'D', 'L', 'R', 'F', 'B'], sfx = ['', "'", '2'];
    let out = [], last = null;
    for (let i = 0; i < n; i++) { let f; do { f = faces[(Math.random() * 6) | 0]; } while (f === last); last = f; out.push(f + sfx[(Math.random() * 3) | 0]); }
    return out.join(' ');
  }

  function solveNow() {
    const fac = faceletsFromNet();
    const v = validate(fac);
    if (!v.ok) { setMsg('⚠ ' + v.msg, 'bad'); return; }
    setMsg('計算中…（第一次約需 1 秒）', 'warn');
    setTimeout(() => {
      try {
        const roleModel = E.fromFacelets(v.roleStr);
        const res = S.solve(roleModel, mode);
        if (!res.solvedCheck) throw new Error('unsolved');
        inputRoleStr = v.roleStr; inputUserStr = v.userFac;
        buildSteps(res.stages);
        if (STEPS.length === 0) { setMsg('這個方塊已經是完成狀態了！', 'ok'); return; }
        computeDiagrams();
        $('tabSolve').disabled = false;
        switchTab('solve');
        goFirst();
        renderFullList();
      } catch (err) {
        setMsg('⚠ 這個顏色組合無法還原，可能哪裡貼錯了。請再對照方塊檢查一次。', 'bad');
      }
    }, 30);
  }

  // ---------- 情況小圖示（OLL 黃/灰、PLL 顏色＋箭頭）----------
  const DIAG_HEX = { W: '#f6f7fb', Y: '#ffd400', R: '#d92435', O: '#ff6a12', G: '#08a35a', B: '#1667d8' };
  const DIAG_SPEC = {
    oll: { kind: 'oll' }, ll1: { kind: 'oll' }, ll2: { kind: 'oll' },
    pll: { kind: 'pll', arrows: 'both' }, ll3: { kind: 'pll', arrows: 'corners' }, ll4: { kind: 'pll', arrows: 'edges' },
  };
  function solvedFromCenters(userFac) {
    const cIdx = { U: 4, R: 13, F: 22, D: 31, L: 40, B: 49 };
    let s = '';
    for (const f of FACE_ORDER) s += userFac[cIdx[f]].repeat(9);
    return E.fromFacelets(s);
  }
  function diagramSVG(model, kind, arrowSet, homePos) {
    const topC = E.stickerAt(model, [0, 1, 0], [0, 1, 0]);
    const G = 22, F = 13, T = 9, N = F * 2 + G * 3;
    const gx = (c) => F + c * G, gy = (r) => F + r * G;
    const fillOf = (c) => DIAG_HEX[c] || '#333';
    const rect = (x, y, w, h, fill) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3" fill="${fill}" stroke="#0a0d16" stroke-width="1.4"/>`;
    let cells = '', flaps = '', arrows = '';
    const pieces = model.filter((cu) => cu.pos[1] === 1);
    for (const cu of pieces) {
      for (const s of cu.stickers) {
        const d = s.dir;
        const fill = kind === 'oll' ? (s.c === topC ? fillOf('Y') : '#2b2f3a') : fillOf(s.c);
        if (d[1] === 1) cells += rect(gx(cu.pos[0] + 1), gy(cu.pos[2] + 1), G, G, fill);
        else if (d[2] === -1) flaps += rect(gx(cu.pos[0] + 1), F - T - 2, G, T, fill);
        else if (d[2] === 1) flaps += rect(gx(cu.pos[0] + 1), F + 3 * G + 2, G, T, fill);
        else if (d[0] === -1) flaps += rect(F - T - 2, gy(cu.pos[2] + 1), T, G, fill);
        else if (d[0] === 1) flaps += rect(F + 3 * G + 2, gy(cu.pos[2] + 1), T, G, fill);
      }
    }
    if (kind === 'pll' && homePos) {
      for (const cu of pieces) {
        const corner = cu.stickers.length === 3;
        if (arrowSet === 'corners' && !corner) continue;
        if (arrowSet === 'edges' && corner) continue;
        const hp = homePos[cu.stickers.map((s) => s.c).sort().join('')];
        if (!hp || (hp[0] === cu.pos[0] && hp[2] === cu.pos[2])) continue;
        const x1 = gx(cu.pos[0] + 1) + G / 2, y1 = gy(cu.pos[2] + 1) + G / 2;
        const x2 = gx(hp[0] + 1) + G / 2, y2 = gy(hp[2] + 1) + G / 2;
        arrows += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#fff" stroke-width="2.4" marker-end="url(#ah)"/>`;
      }
    }
    return `<svg viewBox="0 0 ${N} ${N}"><defs><marker id="ah" markerWidth="7" markerHeight="7" refX="5.5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#fff"/></marker></defs>${flaps}${cells}${arrows}</svg>`;
  }
  function computeDiagrams() {
    const solvedUser = solvedFromCenters(inputUserStr);
    const homePos = {};
    for (const cu of solvedUser) homePos[cu.stickers.map((s) => s.c).sort().join('')] = cu.pos;
    let acc = 0;
    for (const st of STAGE_LIST) {
      st.startIdx = acc; acc += st.count;
      const spec = DIAG_SPEC[st.id];
      st.diagram = spec ? diagramSVG(rebuildTo(st.startIdx), spec.kind, spec.arrows, homePos) : '';
    }
  }

  function renderFullList() {
    const el = $('fullList');
    let html = ''; let stageName = '';
    STEPS.forEach((s, i) => {
      if (s.stageTitle !== stageName) { stageName = s.stageTitle; html += `<div style="margin-top:6px;color:var(--accent);font-weight:700">${stageName}</div>`; }
      html += `<code>${s.notation}</code> `;
    });
    el.innerHTML = html;
  }

  function switchTab(which) {
    const inp = which === 'input';
    $('pageInput').classList.toggle('hidden', !inp);
    $('pageSolve').classList.toggle('hidden', inp);
    $('tabInput').classList.toggle('active', inp);
    $('tabSolve').classList.toggle('active', !inp);
  }

  // ---------- 視角拖曳 ----------
  let rx = -27, ry = -32, drag = null;
  const scene = $('scene');
  function applyView() { if (!animating) cubeEl.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`; else cubeEl.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`; }
  cubeEl.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`;
  function ptr(e) { return e.touches ? e.touches[0] : e; }
  scene.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY, rx, ry }; scene.setPointerCapture(e.pointerId); });
  scene.addEventListener('pointermove', (e) => {
    if (!drag) return;
    ry = drag.ry + (e.clientX - drag.x) * 0.5;
    rx = drag.rx - (e.clientY - drag.y) * 0.5;
    rx = Math.max(-85, Math.min(85, rx));
    cubeEl.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg)`;
  });
  scene.addEventListener('pointerup', () => { drag = null; });
  scene.addEventListener('pointercancel', () => { drag = null; });

  // ---------- 初始化 ----------
  buildNet();
  // 預覽用：解法頁一開始顯示打亂樣子由 solveNow 帶入
  window.__RC = {
    validate, faceletsFromNet, loadFacelets, solveNow, get STEPS() { return STEPS; },
    dbgMove(facStr, face, quarter, ms) {
      $('pageSolve').classList.remove('hidden'); $('pageInput').classList.add('hidden');
      const model = E.fromFacelets(facStr);
      renderCube(model);
      requestAnimationFrame(() => animateMove(model, { face, quarter }, ms || 500));
    },
  }; // debug 用
})();
