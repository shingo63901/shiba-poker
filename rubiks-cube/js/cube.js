(function(){
// ==========================================================================
// 魔術方塊引擎（幾何模型）— 供求解器與 3D 動畫共用
// 座標系：+y=U(上) -y=D(下) +x=R(右) -x=L(左) +z=F(前) -z=B(後)
// 面轉定義為「從該面外側看順時針」= 繞外法線 -90°
// ==========================================================================
'use strict';

// --- 90 度整數旋轉 ---
// dir=+1 表示 +90（右手定則繞 +axis），dir=-1 表示 -90
function rot(v, axis, dir) {
  const [x, y, z] = v;
  if (axis === 'x') return dir > 0 ? [x, -z, y] : [x, z, -y];
  if (axis === 'y') return dir > 0 ? [z, y, -x] : [-z, y, x];
  return dir > 0 ? [-y, x, z] : [y, -x, z]; // z
}
const eq = (a, b) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];

// 每個面轉：作用的層（座標軸+值）、旋轉軸、旋轉方向（順時針=從外側看）
const FACE = {
  U: { axis: 'y', val: 1, ra: 'y', rd: -1 },
  D: { axis: 'y', val: -1, ra: 'y', rd: +1 },
  R: { axis: 'x', val: 1, ra: 'x', rd: -1 },
  L: { axis: 'x', val: -1, ra: 'x', rd: +1 },
  F: { axis: 'z', val: 1, ra: 'z', rd: -1 },
  B: { axis: 'z', val: -1, ra: 'z', rd: +1 },
};

// 標準配色（角色→顏色字母）。U=黃 D=白 F=綠 B=藍 R=紅 L=橙
const SCHEME = { U: 'Y', D: 'W', F: 'G', B: 'B', R: 'R', L: 'O' };

// 建立已還原方塊：26 個 cubie（略過正中心）
function solvedCube() {
  const cubies = [];
  for (let x = -1; x <= 1; x++)
    for (let y = -1; y <= 1; y++)
      for (let z = -1; z <= 1; z++) {
        if (x === 0 && y === 0 && z === 0) continue;
        const stickers = [];
        if (y === 1) stickers.push({ dir: [0, 1, 0], c: SCHEME.U });
        if (y === -1) stickers.push({ dir: [0, -1, 0], c: SCHEME.D });
        if (x === 1) stickers.push({ dir: [1, 0, 0], c: SCHEME.R });
        if (x === -1) stickers.push({ dir: [-1, 0, 0], c: SCHEME.L });
        if (z === 1) stickers.push({ dir: [0, 0, 1], c: SCHEME.F });
        if (z === -1) stickers.push({ dir: [0, 0, -1], c: SCHEME.B });
        cubies.push({ pos: [x, y, z], stickers });
      }
  return cubies;
}

function clone(cube) {
  return cube.map((c) => ({
    pos: c.pos.slice(),
    stickers: c.stickers.map((s) => ({ dir: s.dir.slice(), c: s.c })),
  }));
}

// 套用單一面轉（quarter：1=順時針, 2=180, 3=逆時針/prime）
function applyFace(cube, face, quarter = 1) {
  const f = FACE[face];
  const idx = f.axis === 'x' ? 0 : f.axis === 'y' ? 1 : 2;
  for (let q = 0; q < quarter; q++) {
    for (const cu of cube) {
      if (cu.pos[idx] !== f.val) continue;
      cu.pos = rot(cu.pos, f.ra, f.rd);
      for (const s of cu.stickers) s.dir = rot(s.dir, f.ra, f.rd);
    }
  }
  return cube;
}

// ---- 完整轉法（面 / 寬轉 / 中層 / 整體旋轉）供 CFOP 公式使用 ----
// spec：作用哪些層（該軸座標）、旋轉軸、旋轉方向
const MOVE_SPEC = {
  U: { axis: 'y', layers: [1], rd: -1 }, D: { axis: 'y', layers: [-1], rd: 1 },
  R: { axis: 'x', layers: [1], rd: -1 }, L: { axis: 'x', layers: [-1], rd: 1 },
  F: { axis: 'z', layers: [1], rd: -1 }, B: { axis: 'z', layers: [-1], rd: 1 },
  M: { axis: 'x', layers: [0], rd: 1 }, E: { axis: 'y', layers: [0], rd: 1 }, S: { axis: 'z', layers: [0], rd: -1 },
  r: { axis: 'x', layers: [1, 0], rd: -1 }, l: { axis: 'x', layers: [-1, 0], rd: 1 },
  u: { axis: 'y', layers: [1, 0], rd: -1 }, d: { axis: 'y', layers: [-1, 0], rd: 1 },
  f: { axis: 'z', layers: [1, 0], rd: -1 }, b: { axis: 'z', layers: [-1, 0], rd: 1 },
  x: { axis: 'x', layers: [1, 0, -1], rd: -1 }, y: { axis: 'y', layers: [1, 0, -1], rd: -1 }, z: { axis: 'z', layers: [1, 0, -1], rd: -1 },
};
function applyMove(cube, token, quarter = 1) {
  const spec = MOVE_SPEC[token];
  if (!spec) return cube;
  const idx = spec.axis === 'x' ? 0 : spec.axis === 'y' ? 1 : 2;
  for (let q = 0; q < quarter; q++) {
    for (const cu of cube) {
      if (spec.layers.indexOf(cu.pos[idx]) === -1) continue;
      cu.pos = rot(cu.pos, spec.axis, spec.rd);
      for (const s of cu.stickers) s.dir = rot(s.dir, spec.axis, spec.rd);
    }
  }
  return cube;
}

// 解析 move 字串（支援 R U R' / Rw r M x y z / U2 …）→ [{move,quarter}]
function parseMoves(str) {
  if (!str) return [];
  return str
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((m) => {
      let quarter = 1;
      if (m.indexOf('2') !== -1) quarter = 2;
      else if (m.indexOf("'") !== -1) quarter = 3;
      let base = m.replace(/['2]/g, '');
      if (base.length === 2 && base[1] === 'w') base = base[0].toLowerCase(); // Rw → r
      return { move: base, quarter };
    });
}
function applyMoves(cube, str) {
  for (const mv of parseMoves(str)) applyMove(cube, mv.move, mv.quarter);
  return cube;
}
function invertMoves(str) {
  return parseMoves(str)
    .reverse()
    .map((m) => m.move + (m.quarter === 1 ? "'" : m.quarter === 2 ? '2' : ''))
    .join(' ');
}

// --- Facelet I/O ---
// 面內 3x3（row-major，正對該面看）→ (position, normal) 對照
// 網格：面對每個面時，該面的 (row,col) 對應哪個 cubie 座標。
// 定義各面「往右 u 向量、往下 v 向量、法線 n」
const FACE_BASIS = {
  U: { n: [0, 1, 0], u: [1, 0, 0], v: [0, 0, 1] }, // 上面：右=+x, 下(往B)= +z
  D: { n: [0, -1, 0], u: [1, 0, 0], v: [0, 0, -1] },
  F: { n: [0, 0, 1], u: [1, 0, 0], v: [0, -1, 0] },
  B: { n: [0, 0, -1], u: [-1, 0, 0], v: [0, -1, 0] },
  R: { n: [1, 0, 0], u: [0, 0, -1], v: [0, -1, 0] },
  L: { n: [-1, 0, 0], u: [0, 0, 1], v: [0, -1, 0] },
};
const FACE_ORDER = ['U', 'R', 'F', 'D', 'L', 'B'];

function stickerAt(cube, pos, normal) {
  for (const cu of cube) {
    if (!eq(cu.pos, pos)) continue;
    for (const s of cu.stickers) if (eq(s.dir, normal)) return s.c;
  }
  return null;
}

// 取得 54 facelet 字串（URFDLB，每面 9 格 row-major）
function toFacelets(cube) {
  let out = '';
  for (const face of FACE_ORDER) {
    const b = FACE_BASIS[face];
    for (let r = -1; r <= 1; r++)
      for (let c = -1; c <= 1; c++) {
        const pos = [
          b.n[0] + b.u[0] * c + b.v[0] * r,
          b.n[1] + b.u[1] * c + b.v[1] * r,
          b.n[2] + b.u[2] * c + b.v[2] * r,
        ];
        out += stickerAt(cube, pos, b.n);
      }
  }
  return out;
}

// 從 54 facelet 字串（URFDLB 序）建立 cube 模型
function fromFacelets(str) {
  const byPos = {}; // key pos.join -> {pos, stickers:[]}
  let i = 0;
  for (const face of FACE_ORDER) {
    const b = FACE_BASIS[face];
    for (let r = -1; r <= 1; r++)
      for (let c = -1; c <= 1; c++) {
        const pos = [
          b.n[0] + b.u[0] * c + b.v[0] * r,
          b.n[1] + b.u[1] * c + b.v[1] * r,
          b.n[2] + b.u[2] * c + b.v[2] * r,
        ];
        const col = str[i++];
        const k = pos.join(',');
        if (!byPos[k]) byPos[k] = { pos, stickers: [] };
        byPos[k].stickers.push({ dir: b.n.slice(), c: col });
      }
  }
  return Object.values(byPos);
}

const _exports = {
  rot, FACE, MOVE_SPEC, SCHEME, solvedCube, clone, applyFace, applyMove, parseMoves,
  applyMoves, invertMoves, toFacelets, fromFacelets, FACE_BASIS, FACE_ORDER, stickerAt, eq,
};
if (typeof module !== 'undefined' && module.exports) module.exports = _exports;
if (typeof window !== 'undefined') window.RCube = _exports;

})();
