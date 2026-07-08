(function(){
// ==========================================================================
// 新手層先法（LBL）求解器
//  - 底十字 + 第一層 + 中層：逐塊 IDA* 搜尋（保證正確、保留已完成部分）
//  - 頂層（黃面）：兩段式 OLL + PLL，用「巨集 BFS」保證涵蓋所有情況
// 回傳分階段的解法，供教學逐步播放
// ==========================================================================
'use strict';
const E = (typeof require !== 'undefined') ? require('./cube.js') : window.RCube;
const ALGS = (typeof require !== 'undefined') ? require('./algs.js') : window.CFOP_ALGS;
const { solvedCube, clone, applyFace, eq } = E;

// ---- 參考：已還原方塊中每個塊的「家」 ----
const REF = solvedCube();
function pieceKey(colors) { return colors.slice().sort().join(''); }
function collectPieces(cube, nSt) {
  const out = {};
  for (const cu of cube) {
    if (cu.stickers.length !== nSt) continue;
    const colors = cu.stickers.map((s) => s.c);
    out[pieceKey(colors)] = cu;
  }
  return out;
}
const REF_EDGES = collectPieces(REF, 2);
const REF_CORNERS = collectPieces(REF, 3);

function findPiece(cube, colors) {
  const key = pieceKey(colors);
  for (const cu of cube) {
    if (cu.stickers.length !== colors.length) continue;
    if (pieceKey(cu.stickers.map((s) => s.c)) === key) return cu;
  }
  return null;
}
// 某塊是否已歸位（位置 + 每個貼紙朝向皆與參考相同）
function pieceSolved(cube, colors) {
  const ref = (colors.length === 2 ? REF_EDGES : REF_CORNERS)[pieceKey(colors)];
  const cur = findPiece(cube, colors);
  if (!eq(cur.pos, ref.pos)) return false;
  for (const rs of ref.stickers) {
    const cs = cur.stickers.find((s) => s.c === rs.c);
    if (!eq(cs.dir, rs.dir)) return false;
  }
  return true;
}

// ---- IDA* 逐塊搜尋（含單塊距離啟發式）----
const ALL_FACES = ['U', 'D', 'L', 'R', 'F', 'B'];
const OPP = { U: 'D', D: 'U', L: 'R', R: 'L', F: 'B', B: 'F' };
const AXIS_IDX = { x: 0, y: 1, z: 2 };
const enc = (pos, dir) => pos.join(',') + ';' + dir.join(',');

// 單塊（pos + 指定顏色貼紙朝向）距離表：從該塊的「家」BFS，純幾何轉移
const DIST_CACHE = new Map();
function pieceDistMap(colors, allowedFaces = ALL_FACES) {
  const ck = pieceKey(colors) + '@' + allowedFaces.join('');
  if (DIST_CACHE.has(ck)) return DIST_CACHE.get(ck);
  const ref = (colors.length === 2 ? REF_EDGES : REF_CORNERS)[pieceKey(colors)];
  const c1 = colors[0];
  const homePos = ref.pos;
  const homeDir = ref.stickers.find((s) => s.c === c1).dir;
  const start = enc(homePos, homeDir);
  const dist = new Map([[start, 0]]);
  const decode = (k) => {
    const [p, d] = k.split(';');
    return [p.split(',').map(Number), d.split(',').map(Number)];
  };
  const q = [start]; let qi = 0;
  while (qi < q.length) {
    const cur = q[qi++];
    const d0 = dist.get(cur);
    const [pos, dir] = decode(cur);
    for (const face of allowedFaces) {
      const f = E.FACE[face];
      const idx = AXIS_IDX[f.axis];
      for (let quarter = 1; quarter <= 3; quarter++) {
        let p = pos, dd = dir;
        for (let t = 0; t < quarter; t++) {
          if (p[idx] === f.val) { p = E.rot(p, f.ra, f.rd); dd = E.rot(dd, f.ra, f.rd); }
        }
        const nk = enc(p, dd);
        if (!dist.has(nk)) { dist.set(nk, d0 + 1); q.push(nk); }
      }
    }
  }
  DIST_CACHE.set(ck, dist);
  return dist;
}
function nodeOf(cube, colors) {
  const cu = findPiece(cube, colors);
  const dir = cu.stickers.find((s) => s.c === colors[0]).dir;
  return enc(cu.pos, dir);
}

// ---- 整數編碼：單塊 (pos,dir) 壓成 byte，並預算 18 步轉移表 ----
const DIRS = [[0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1]];
function dirCode(d) { for (let i = 0; i < 6; i++) if (eq(DIRS[i], d)) return i; return -1; }
const posCode = (p) => (p[0] + 1) + 3 * (p[1] + 1) + 9 * (p[2] + 1); // 0..26
const byteOf = (pos, dir) => posCode(pos) * 8 + dirCode(dir);       // 0..221
const MOVES18 = [];
for (const face of ALL_FACES) for (let quarter = 1; quarter <= 3; quarter++) MOVES18.push({ face, quarter });
const TT = new Int16Array(222 * 18).fill(-1); // TT[byte*18+moveIdx] = newByte
(function buildTT() {
  for (let pc = 0; pc < 27; pc++) {
    const pos = [(pc % 3) - 1, ((pc / 3 | 0) % 3) - 1, ((pc / 9 | 0) % 3) - 1];
    for (let dc = 0; dc < 6; dc++) {
      const b = pc * 8 + dc;
      for (let mi = 0; mi < 18; mi++) {
        const mv = MOVES18[mi], f = E.FACE[mv.face], idx = AXIS_IDX[f.axis];
        let p = pos, d = DIRS[dc];
        for (let t = 0; t < mv.quarter; t++)
          if (p[idx] === f.val) { p = E.rot(p, f.ra, f.rd); d = E.rot(d, f.ra, f.rd); }
        TT[b * 18 + mi] = byteOf(p, d);
      }
    }
  }
})();

// 多塊「聯合」精確距離表（整數 key、預算轉移表，BFS 極快）
const JOINT_CACHE = new Map();
function packBytes(bytes) { let k = 0; for (let i = 0; i < bytes.length; i++) k = k * 256 + bytes[i]; return k; }
function startBytes(targetSet) {
  return targetSet.map((cs) => {
    const ref = (cs.length === 2 ? REF_EDGES : REF_CORNERS)[pieceKey(cs)];
    return byteOf(ref.pos, ref.stickers.find((s) => s.c === cs[0]).dir);
  });
}
function jointDistMap(targetSet, allowedFaces = ALL_FACES) {
  const ck = targetSet.map(pieceKey).join('#') + '@' + allowedFaces.join('');
  if (JOINT_CACHE.has(ck)) return JOINT_CACHE.get(ck);
  const moveIdx = [];
  for (let mi = 0; mi < 18; mi++) if (allowedFaces.includes(MOVES18[mi].face)) moveIdx.push(mi);
  const n = targetSet.length;
  const sb = startBytes(targetSet);
  const dist = new Map([[packBytes(sb), 0]]);
  const q = [sb]; let qi = 0;
  while (qi < q.length) {
    const cur = q[qi++];
    const d0 = dist.get(packBytes(cur));
    for (const mi of moveIdx) {
      const nb = new Array(n);
      for (let i = 0; i < n; i++) nb[i] = TT[cur[i] * 18 + mi];
      const nk = packBytes(nb);
      if (!dist.has(nk)) { dist.set(nk, d0 + 1); q.push(nb); }
    }
  }
  JOINT_CACHE.set(ck, dist);
  return dist;
}
function jointNode(cube, targetSet) {
  const bytes = targetSet.map((cs) => {
    const cu = findPiece(cube, cs);
    return byteOf(cu.pos, cu.stickers.find((s) => s.c === cs[0]).dir);
  });
  return packBytes(bytes);
}

// IDA*：把 targetSet（一組塊）全部歸位，且 lockedList 內各塊保持歸位
// allowedFaces：限制可用的面（預設全部 6 面）
function idaSolveSet(cube, targetSet, lockedList, maxDepth = 14, allowedFaces = ALL_FACES) {
  const jmap = jointDistMap(targetSet, allowedFaces);
  const lmaps = lockedList.map((c) => pieceDistMap(c, allowedFaces));
  const BIG = 99;
  function h() {
    let m = jmap.get(jointNode(cube, targetSet));
    if (m === undefined) m = BIG;
    for (let i = 0; i < lockedList.length; i++) {
      const d = lmaps[i].get(nodeOf(cube, lockedList[i]));
      if ((d === undefined ? BIG : d) > m) m = d === undefined ? BIG : d;
    }
    return m;
  }
  const path = [];
  let nextBound;
  function dfs(g, bound, lastFace) {
    const hv = h();
    const f = g + hv;
    if (f > bound) { if (f < nextBound) nextBound = f; return false; }
    if (hv === 0) return true;
    for (const face of allowedFaces) {
      if (face === lastFace) continue;
      if (OPP[face] === lastFace && face < lastFace) continue;
      for (let quarter = 1; quarter <= 3; quarter++) {
        applyFace(cube, face, quarter);
        path.push({ face, quarter });
        if (dfs(g + 1, bound, face)) return true;
        path.pop();
        applyFace(cube, face, (4 - quarter) % 4 || 4);
      }
    }
    return false;
  }
  let bound = h();
  while (bound <= maxDepth) {
    nextBound = Infinity;
    path.length = 0;
    if (dfs(0, bound, null)) {
      const sol = path.slice();
      // 還原 cube 到呼叫前狀態（讓呼叫端自行套用 sol）
      for (let i = sol.length - 1; i >= 0; i--) applyFace(cube, sol[i].face, inv(sol[i].quarter));
      return sol;
    }
    bound = nextBound;
  }
  return null;
}
function idaSolvePiece(cube, targetColors, lockedList, maxDepth = 14) {
  return idaSolveSet(cube, [targetColors], lockedList, maxDepth);
}

// ---- 角色顏色（依 SCHEME）----
const WHITE = E.SCHEME.D, YELLOW = E.SCHEME.U;
const SIDES = [E.SCHEME.F, E.SCHEME.R, E.SCHEME.B, E.SCHEME.L]; // G R B O
// 相鄰側色配對（用於中層邊、頂層）
function adjacentSidePairs() {
  // F-R, R-B, B-L, L-F
  return [
    [E.SCHEME.F, E.SCHEME.R],
    [E.SCHEME.R, E.SCHEME.B],
    [E.SCHEME.B, E.SCHEME.L],
    [E.SCHEME.L, E.SCHEME.F],
  ];
}

// 統一取得 move token（相容舊 {face} 與新 {move}）
const tk = (m) => m.move || m.face;
// 化簡：合併同面連續轉動、消去互逆（僅限單面 UDLRFB；寬轉/中層/旋轉不動）
function simplifyMoves(mvs) {
  const st = [];
  for (const mv of mvs) {
    const t = tk(mv);
    const m = { move: t, quarter: mv.quarter };
    let merged = false;
    if (OPP[t]) { // 只對基本面做化簡
      if (st.length && st[st.length - 1].move === t) {
        const q = (st[st.length - 1].quarter + m.quarter) % 4;
        st.pop();
        if (q !== 0) st.push({ move: t, quarter: q });
        merged = true;
      } else if (st.length >= 2 && OPP[st[st.length - 1].move] === t &&
                 st[st.length - 2].move === t) {
        const q = (st[st.length - 2].quarter + m.quarter) % 4;
        const opp = st.pop(); st.pop();
        if (q !== 0) st.push({ move: t, quarter: q });
        st.push(opp);
        merged = true;
      }
    }
    if (!merged) st.push(m);
  }
  return st;
}

function movesToStr(mvs) {
  return mvs
    .map((m) => tk(m) + (m.quarter === 1 ? '' : m.quarter === 2 ? '2' : "'"))
    .join(' ');
}

// ---- F2L：先把配對塊「挖」到頂層，再用限定面搜尋插入 ----
const DIR_OF_FACE = { U: [0, 1, 0], D: [0, -1, 0], R: [1, 0, 0], L: [-1, 0, 0], F: [0, 0, 1], B: [0, 0, -1] };
function faceOfDir(d) { for (const k in DIR_OF_FACE) if (eq(DIR_OF_FACE[k], d)) return k; return null; }
const FACE_OF_COLOR = {};
for (const f in E.SCHEME) FACE_OF_COLOR[E.SCHEME[f]] = f;

function doMoves(cube, log, mvs) { for (const m of mvs) { applyFace(cube, m.face, m.quarter); log.push(m); } }
function inv(q) { return (4 - q) % 4 || 4; }

// 把某塊從下兩層挖到頂層（保留 keepList 內各塊）
function popToTop(cube, log, colors, keepList) {
  const cu = findPiece(cube, colors);
  if (cu.pos[1] === 1) return true;
  const gs = [];
  if (cu.pos[0] !== 0) gs.push(faceOfDir([cu.pos[0], 0, 0]));
  if (cu.pos[2] !== 0) gs.push(faceOfDir([0, 0, cu.pos[2]]));
  for (const g of gs) for (const uq of [1, 3, 2]) for (const q of [1, 3]) {
    const trial = [{ face: g, quarter: q }, { face: 'U', quarter: uq }, { face: g, quarter: inv(q) }];
    const c2 = clone(cube);
    for (const m of trial) applyFace(c2, m.face, m.quarter);
    if (findPiece(c2, colors).pos[1] !== 1) continue;
    if (!keepList.every((k) => pieceSolved(c2, k))) continue;
    doMoves(cube, log, trial);
    return true;
  }
  return false;
}

// 解一個 F2L 槽（corner+edge），locked 為必須保留的塊
function solveF2LSlot(cube, log, corner, edge, fa, fb, locked) {
  const allow = [fa, fb, 'U'];
  for (let guard = 0; guard < 8; guard++) {
    if (pieceSolved(cube, corner) && pieceSolved(cube, edge)) return true;
    // 先確保兩塊都在頂層（或已歸位）
    if (!pieceSolved(cube, corner) && findPiece(cube, corner).pos[1] !== 1) {
      if (!popToTop(cube, log, corner, locked)) return false;
      continue;
    }
    if (!pieceSolved(cube, edge) && findPiece(cube, edge).pos[1] !== 1) {
      if (!popToTop(cube, log, edge, locked)) return false;
      continue;
    }
    const mv = idaSolveSet(cube, [corner, edge], locked, 13, allow);
    if (!mv) return false;
    doMoves(cube, log, mv);
    return pieceSolved(cube, corner) && pieceSolved(cube, edge);
  }
  return false;
}

// ---- 巨集 BFS（頂層）----
function applyMacroSeq(cube, seqStr) { E.applyMoves(cube, seqStr); }
function stateKey(cube) { return E.toFacelets(cube); }

function macroBFS(cube, macros, isGoal, maxDepth = 9) {
  // macros: [{name, str}]；回傳達成 isGoal 的巨集序列（合併後的 move 陣列）
  if (isGoal(cube)) return [];
  const start = stateKey(cube);
  const seen = new Set([start]);
  const q = [{ key: start, path: [] }];
  const cache = new Map([[start, cube]]);
  while (q.length) {
    const cur = q.shift();
    if (cur.path.length >= maxDepth) continue;
    for (const mac of macros) {
      const c2 = clone(cache.get(cur.key));
      applyMacroSeq(c2, mac.str);
      const k2 = stateKey(c2);
      if (seen.has(k2)) continue;
      const path2 = cur.path.concat([mac]);
      if (isGoal(c2)) return path2;
      seen.add(k2);
      cache.set(k2, c2);
      q.push({ key: k2, path: path2 });
    }
  }
  return null;
}

// ==========================================================================
// 主求解
// ==========================================================================
function solve(scrambleFaceletsCubeOrMoves) {
  // 接受 cube 物件
  const cube = clone(scrambleFaceletsCubeOrMoves);
  const stages = []; // {id,title,moves:[{face,quarter}], desc}

  const fallbacks = {};
  function record(id, title, mvs, desc, noSimplify) {
    const norm = (mvs || []).map((m) => ({ move: m.move || m.face, quarter: m.quarter }));
    const sm = noSimplify ? norm : simplifyMoves(norm);
    if (sm.length) stages.push({ id, title, moves: sm, desc });
  }
  function applyStep(mvs) { for (const m of mvs) E.applyMove(cube, m.move || m.face, m.quarter); }
  function runSet(targetSet, locked, id, title, desc, maxD) {
    const mvs = idaSolveSet(cube, targetSet, locked, maxD || 14);
    if (mvs === null) throw new Error('IDA fail ' + title);
    for (const m of mvs) applyFace(cube, m.face, m.quarter);
    record(id, title, mvs, desc);
    return mvs;
  }

  // ---- 1. 底部白十字（四邊一起，最佳解 ≤8 步）----
  const crossEdges = SIDES.map((s) => [WHITE, s]);
  runSet(crossEdges, [], 'cross', '底部白十字', '把四個白色邊塊排成十字', 10);

  // ---- 2+3. 第一、二層：逐一放入「角+邊」配對（F2L）----
  const slots = [
    { c: [WHITE, E.SCHEME.F, E.SCHEME.R], e: [E.SCHEME.F, E.SCHEME.R], fa: 'F', fb: 'R' },
    { c: [WHITE, E.SCHEME.R, E.SCHEME.B], e: [E.SCHEME.R, E.SCHEME.B], fa: 'R', fb: 'B' },
    { c: [WHITE, E.SCHEME.B, E.SCHEME.L], e: [E.SCHEME.B, E.SCHEME.L], fa: 'B', fb: 'L' },
    { c: [WHITE, E.SCHEME.L, E.SCHEME.F], e: [E.SCHEME.L, E.SCHEME.F], fa: 'L', fb: 'F' },
  ];
  const locked = crossEdges.slice();
  let si = 0;
  for (const slot of slots) {
    si++;
    const log = [];
    const ok = solveF2LSlot(cube, log, slot.c, slot.e, slot.fa, slot.fb, locked.slice());
    if (!ok) throw new Error('F2L slot ' + si + ' failed');
    record('f2l', '前兩層配對 ' + si, log,
      '把白色角塊和它旁邊的中層邊塊，一起放進正確的位置');
    locked.push(slot.c, slot.e);
  }

  // ---- 4. OLL：一個公式把整個頂面轉成黃色 ----
  {
    const r = solveOLL(cube);
    if (r) { applyStep(r.moves); record('oll', 'OLL ' + r.label, r.moves, r.desc, true); }
    else {
      fallbacks.oll = true; fallbacks.ollState = E.toFacelets(cube);
      const mvs = twoLookOLL(cube);
      record('oll', '頂面轉正（兩段式）', mvs, '先做黃十字，再把黃角轉正', true);
    }
  }

  // ---- 5. PLL：一個公式把頂層排到正確位置 ----
  {
    const r = solvePLL(cube);
    if (r) { applyStep(r.moves); record('pll', 'PLL ' + r.label, r.moves, r.desc, true); }
    else {
      fallbacks.pll = true; fallbacks.pllState = E.toFacelets(cube);
      const mvs = twoLookPLL(cube);
      record('pll', '頂層排列（兩段式）', mvs, '先排角、再排邊', true);
    }
  }

  if (!isSolved(cube)) throw new Error('NOT SOLVED at end');
  return { stages, solvedCheck: isSolved(cube), fallbacks };
}

// ---- CFOP 頂層辨識（套用後驗證，保證正確）----
function solveOLL(cube) {
  if (allYellowUp(cube)) return { moves: [], label: '（跳過）', desc: '頂面本來就全是黃色，這一步不用做。' };
  for (let auf = 0; auf < 4; auf++) {
    for (const o of ALGS.OLL) {
      const c = clone(cube);
      if (auf) E.applyMove(c, 'U', auf);
      E.applyMoves(c, o.alg);
      if (allYellowUp(c)) {
        const moves = [];
        if (auf) moves.push({ move: 'U', quarter: auf });
        moves.push(...E.parseMoves(o.alg));
        return { moves, label: '#' + o.n + (o.name ? '（' + o.name + '）' : ''), desc: '用一個公式，把整個頂面一次轉成黃色。' };
      }
    }
  }
  return null;
}
function solvePLL(cube) {
  // PLL 跳過：頂層本來就排好，只需（可能）轉一下頂層對齊
  for (let post = 0; post < 4; post++) {
    const c = clone(cube); if (post) E.applyMove(c, 'U', post);
    if (isSolved(c)) return { moves: post ? [{ move: 'U', quarter: post }] : [], label: '（跳過）', desc: '頂層已經排好，' + (post ? '把頂層轉一下對齊就完成。' : '直接完成！') };
  }
  for (let pre = 0; pre < 4; pre++) {
    for (const p of ALGS.PLL) {
      const c0 = clone(cube);
      if (pre) E.applyMove(c0, 'U', pre);
      E.applyMoves(c0, p.alg);
      for (let post = 0; post < 4; post++) {
        const c2 = clone(c0);
        if (post) E.applyMove(c2, 'U', post);
        if (isSolved(c2)) {
          const moves = [];
          if (pre) moves.push({ move: 'U', quarter: pre });
          moves.push(...E.parseMoves(p.alg));
          if (post) moves.push({ move: 'U', quarter: post });
          return { moves, label: p.name + '-perm', desc: '用一個公式，把頂層的角和邊一次排到正確位置。' };
        }
      }
    }
  }
  return null;
}
// 後備：兩段式（保證能解，供辨識失敗時使用）
const OLL_EDGE_MACROS = [
  { name: 'U', str: 'U' }, { name: 'U2', str: 'U2' }, { name: "U'", str: "U'" },
  { name: 'FRUF', str: "F R U R' U' F'" },
];
const OLL_CORNER_MACROS = [
  { name: 'U', str: 'U' }, { name: 'U2', str: 'U2' }, { name: "U'", str: "U'" },
  { name: 'Sune', str: "R U R' U R U2 R'" },
];
const PLL_MACROS = [
  { name: 'U', str: 'U' }, { name: 'U2', str: 'U2' }, { name: "U'", str: "U'" },
  { name: 'CornerCycle', str: "R' F R' B2 R F' R' B2 R2" },
  { name: 'EdgeCycle', str: "R U' R U R U R U' R' U' R2" },
];
function twoLookOLL(cube) {
  const out = [];
  for (const [macros, goal, d] of [[OLL_EDGE_MACROS, yellowEdgesOriented, 10], [OLL_CORNER_MACROS, allYellowUp, 12]]) {
    const path = macroBFS(cube, macros, goal, d);
    if (path === null) throw new Error('two-look OLL fail');
    const mvs = expandMacros(path);
    for (const m of mvs) E.applyMove(cube, m.move, m.quarter);
    out.push(...mvs);
  }
  return out;
}
function twoLookPLL(cube) {
  const path = macroBFS(cube, PLL_MACROS, isSolved, 14);
  if (path === null) throw new Error('two-look PLL fail');
  const mvs = expandMacros(path);
  for (const m of mvs) E.applyMove(cube, m.move, m.quarter);
  return mvs;
}

// ---- 公式正規化：把含整體旋轉(x/y/z)但沒還原的公式，自動補上還原旋轉 ----
const centerKey = (c) => { const fl = E.toFacelets(c); return fl[4] + fl[13] + fl[22] + fl[31] + fl[40] + fl[49]; };
const ORIENTATIONS = (() => {
  const solvedKey = centerKey(E.solvedCube());
  const res = new Map([[solvedKey, '']]);
  const q = [{ s: '', c: E.solvedCube() }]; let qi = 0;
  while (qi < q.length) {
    const cur = q[qi++];
    for (const r of ['x', 'y', 'z']) {
      const c2 = clone(cur.c); E.applyMove(c2, r, 1);
      const k = centerKey(c2);
      if (!res.has(k)) { const s = (cur.s + ' ' + r).trim(); res.set(k, s); q.push({ s, c: c2 }); }
    }
  }
  return { map: res, solvedKey };
})();
function balanceAlg(alg) {
  const c = E.solvedCube(); E.applyMoves(c, alg);
  const k = centerKey(c);
  if (k === ORIENTATIONS.solvedKey) return alg;
  // 找一個旋轉，套在後面能把中心轉回原位
  for (const [okey, ostr] of ORIENTATIONS.map) {
    const c2 = clone(c); if (ostr) E.applyMoves(c2, ostr);
    if (centerKey(c2) === ORIENTATIONS.solvedKey) return ostr ? (alg + ' ' + ostr) : alg;
  }
  return alg;
}
(function normalizeAlgs() {
  for (const o of ALGS.OLL) o.alg = balanceAlg(o.alg);
  for (const p of ALGS.PLL) p.alg = balanceAlg(p.alg);
})();

// ---- 頂層 goal 輔助 ----
function adjacentSidePairsYellow() {
  return [
    [YELLOW, E.SCHEME.F], [YELLOW, E.SCHEME.R], [YELLOW, E.SCHEME.B], [YELLOW, E.SCHEME.L],
  ];
}
// 黃十字：四個頂層邊「黃色朝上」
function yellowEdgesOriented(cube) {
  for (const cu of cube) {
    if (cu.stickers.length !== 2) continue;
    const yl = cu.stickers.find((s) => s.c === YELLOW);
    if (!yl) continue;
    if (cu.pos[1] !== 1) return false; // 黃色邊必須在頂層
    if (!eq(yl.dir, [0, 1, 0])) return false; // 黃色朝上
  }
  return true;
}
// 頂面全黃：四個頂層角黃色朝上
function allYellowUp(cube) {
  if (!yellowEdgesOriented(cube)) return false;
  for (const cu of cube) {
    if (cu.stickers.length !== 3) continue;
    const yl = cu.stickers.find((s) => s.c === YELLOW);
    if (!yl) continue;
    if (cu.pos[1] !== 1) return false;
    if (!eq(yl.dir, [0, 1, 0])) return false;
  }
  return true;
}
function isSolved(cube) {
  return E.toFacelets(cube) === E.toFacelets(REF);
}
function expandMacros(path) {
  const out = [];
  for (const mac of path) out.push(...E.parseMoves(mac.str));
  return out;
}

const _exports = { solve, movesToStr, simplifyMoves, idaSolvePiece, idaSolveSet, jointDistMap, isSolved, macroBFS };
if (typeof module !== 'undefined' && module.exports) module.exports = _exports;
if (typeof window !== 'undefined') window.RCSolver = _exports;

})();
