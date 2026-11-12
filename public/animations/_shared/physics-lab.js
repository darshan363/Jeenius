/* Jeenius physics-lab shell: canvas picture + controls + live readouts + one "IF this changes -> that changes" line. */
(() => {
const N = '#013062', B = '#e6eeff', W = '#fff', GREEN = '#609a83', RED = '#c75d55', GOLD = '#d8a447', INK = '#202d3d', GREY = '#9aa7b8';
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const H = {
  N, B, W, GREEN, RED, GOLD, INK, GREY, clamp,
  T(c, s, x, y, z = 13, align = 'left', font = 'Saira', color = N) { c.fillStyle = color; c.font = `${z}px ${font},sans-serif`; c.textAlign = align; c.textBaseline = 'alphabetic'; c.fillText(String(s), x, y); },
  L(c, x1, y1, x2, y2, w = 1, color = N, dash = []) { c.save(); c.lineCap = w > 5 ? 'round' : 'butt'; c.strokeStyle = color; c.lineWidth = w; c.setLineDash(dash); c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke(); c.restore(); },
  R(c, x, y, w, h, fill = B, stroke = N, lw = 1.5) { c.save(); if (fill) { c.fillStyle = fill; c.fillRect(x, y, w, h); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw; c.strokeRect(x, y, w, h); } c.restore(); },
  C(c, x, y, r, fill = B, stroke = N, lw = 1.5) { c.save(); c.beginPath(); c.arc(x, y, Math.max(.1, r), 0, Math.PI * 2); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw; c.stroke(); } c.restore(); },
  E(c, x, y, rx, ry, fill = B, stroke = N, lw = 1.5, rot = 0) { c.save(); c.beginPath(); c.ellipse(x, y, Math.max(.1, rx), Math.max(.1, ry), rot, 0, Math.PI * 2); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw; c.stroke(); } c.restore(); },
  A(c, x1, y1, x2, y2, w = 3, color = N) { if (Math.hypot(x2 - x1, y2 - y1) < 4) return; H.L(c, x1, y1, x2, y2, w, color); const a = Math.atan2(y2 - y1, x2 - x1); c.save(); c.fillStyle = color; c.beginPath(); c.moveTo(x2, y2); c.lineTo(x2 - 11 * Math.cos(a - .42), y2 - 11 * Math.sin(a - .42)); c.lineTo(x2 - 11 * Math.cos(a + .42), y2 - 11 * Math.sin(a + .42)); c.closePath(); c.fill(); c.restore(); },
  Tag(c, s, x, y, color = N, align = 'center', z = 14) { c.save(); c.font = `600 ${z}px Saira,sans-serif`; const w = c.measureText(String(s)).width + 14, x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x; c.fillStyle = 'rgba(255,255,255,.95)'; c.fillRect(x0, y - z - 2, w, z + 10); c.strokeStyle = color; c.lineWidth = 1.2; c.strokeRect(x0, y - z - 2, w, z + 10); c.fillStyle = color; c.textAlign = 'left'; c.textBaseline = 'alphabetic'; c.fillText(String(s), x0 + 7, y + 2); c.restore(); },
  P(c, pts, fill = B, stroke = N, lw = 1.5) { c.save(); c.beginPath(); pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.closePath(); if (fill) { c.fillStyle = fill; c.fill(); } if (stroke) { c.strokeStyle = stroke; c.lineWidth = lw; c.stroke(); } c.restore(); },
};

window.PhysicsLab = function PhysicsLab(cfg) {
  document.title = cfg.title + ' · Jeenius';
  document.body.innerHTML = `<main><header class="sh w"><div class="ch"><div class="g">${cfg.tag || 'JEENIUS · SCIENCE'}</div><h1>${cfg.title}</h1></div></header>
  <section class="sh"><div class="ch"><canvas id="cv" aria-label="${cfg.title} animation"></canvas></div></section>
  <aside class="sh"><div class="ch"><h2>CONTROLS</h2><div id="ctl"></div><div class="actions" id="bt"></div><h2>LIVE READOUTS</h2><div id="ro" aria-live="polite"></div></div></aside>
  <footer class="sh w"><div class="ch"><span class="g">FORMULA WITH LIVE NUMBERS</span><div id="fx"></div><div id="chg" aria-live="polite"></div><p class="logic"><strong>LOGIC:</strong> <span id="takeaway"></span></p></div></footer></main>`;

  const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
  const S = {}, M = {}, controls = cfg.controls, els = {};
  controls.forEach(q => S[q.key] = q.value);
  const initial = { ...S };

  const fmt = (q, v) => q.options ? q.options[Math.round(v)] : (Number.isInteger(v) ? v : +v.toFixed(2)) + (q.unit || '');
  function fit() {
    const r = cv.getBoundingClientRect(), d = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.max(1, Math.round(r.width * d)); cv.height = Math.max(1, Math.round(r.width * d * 9 / 16));
    ctx.setTransform(cv.width / 800, 0, 0, cv.height / 450, 0, 0);
  }
  window.addEventListener('resize', fit);

  function restart() { Object.keys(M).forEach(k => delete M[k]); cfg.init(S, M); }

  // ---- controls ----
  const root = document.getElementById('ctl');
  controls.forEach(q => {
    const wrap = document.createElement('div'); wrap.className = 'row'; els[q.key] = { wrap, q };
    const label = document.createElement('label'), name = document.createElement('span'), val = document.createElement('b');
    name.textContent = q.label; label.append(name, val); wrap.append(label); els[q.key].val = val;
    if (q.options) {
      const group = document.createElement('div'); group.className = 'choice';
      els[q.key].btns = q.options.map((o, i) => {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = o;
        b.onclick = () => { S[q.key] = i; if (q.restart !== false) restart(); sync(); };
        group.append(b); return b;
      });
      wrap.append(group);
    } else {
      const input = document.createElement('input'); input.type = 'range'; input.min = q.min; input.max = q.max; input.step = q.step || 1; input.value = q.value; input.setAttribute('aria-label', q.label);
      input.oninput = () => { S[q.key] = +input.value; if (q.restart !== false) restart(); sync(); };
      wrap.append(input); els[q.key].input = input;
    }
    root.append(wrap);
  });
  function sync() {
    controls.forEach(q => {
      const e = els[q.key];
      e.wrap.style.display = q.show && !q.show(S) ? 'none' : '';
      e.val.textContent = q.options ? '' : fmt(q, S[q.key]);
      if (e.input && +e.input.value !== S[q.key]) e.input.value = S[q.key];
      if (e.btns) e.btns.forEach((b, i) => b.setAttribute('aria-pressed', String(i === Math.round(S[q.key]))));
    });
  }

  // ---- buttons ----
  const bt = document.getElementById('bt');
  (cfg.buttons || []).concat([{ label: 'RESET', onClick() { Object.assign(S, initial); restart(); sync(); resetChange(); } }]).forEach((a, i) => {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = a.label; if (i === 0 && cfg.buttons && cfg.buttons.length) b.className = 'primary';
    b.onclick = () => a.onClick(S, M); bt.append(b);
    if (a.dynamicLabel) els['__btn' + i] = { b, a };
  });

  // ---- "IF this changes -> that changes" ----
  const chg = document.getElementById('chg');
  let base = null, baseRes = null, chgTimer = 0, evTimer = 0;
  const resMap = () => { const m = {}; (cfg.results ? cfg.results(S, M) : []).forEach(([k, v]) => m[k] = String(v)); return m; };
  function resetChange() { base = { ...S }; baseRes = resMap(); chg.textContent = ''; }
  function chgText() {
    const ch = controls.filter(q => base[q.key] !== S[q.key] && (!q.show || q.show(S)));
    if (!ch.length) return null;
    const now = resMap(), diffs = [];
    for (const k in now) if (baseRes[k] !== undefined && baseRes[k] !== now[k]) diffs.push(k + ': ' + baseRes[k] + ' → ' + now[k]);
    const sceneChanged = controls.some(q => q.scene && base[q.key] !== S[q.key]);
    return { cond: 'IF ' + ch.map(q => q.label.toLowerCase() + ' ' + fmt(q, base[q.key]) + ' → ' + fmt(q, S[q.key])).join(', '), effect: diffs.length ? diffs.slice(0, 4).join('; ') : (sceneChanged ? 'a different situation, same law' : 'the result stays the same'), now };
  }
  let lastSnap = '';
  function watch() {
    const snap = JSON.stringify(S);
    if (snap === lastSnap) return; lastSnap = snap;
    if (!base) { resetChange(); return; }
    clearTimeout(chgTimer); clearTimeout(evTimer);
    chgTimer = setTimeout(() => {
      if (controls.some(q => q.scene && base[q.key] !== S[q.key])) { chg.textContent = ''; base = { ...S }; baseRes = resMap(); return; }
      const t = chgText(); if (!t) return;
      chg.textContent = t.cond + '  ⇒  ' + t.effect;
      base = { ...S }; baseRes = t.now;
      evTimer = setTimeout(() => { try { window.parent.postMessage({ type: 'jeenius-event', summary: ('student changed ' + t.cond.slice(3) + '; ' + t.effect).slice(0, 290) }, '*'); } catch (_) {} }, 600);
    }, 400);
  }

  // ---- loop ----
  let last = 0, lastRo = '', lastFx = '', lastTx = '';
  function frame(ts) {
    const dt = Math.min(.05, (ts - last) / 1000 || 0); last = ts;
    cfg.step(S, M, dt);
    ctx.clearRect(0, 0, 800, 450); ctx.fillStyle = W; ctx.fillRect(0, 0, 800, 450);
    ctx.save(); ctx.globalAlpha = .07; for (let x = 0; x <= 800; x += 25) H.L(ctx, x, 0, x, 450, .5); for (let y = 0; y <= 450; y += 25) H.L(ctx, 0, y, 800, y, .5); ctx.restore();
    cfg.draw(ctx, S, M, H);
    const ro = cfg.readouts(S, M), roKey = JSON.stringify(ro);
    if (roKey !== lastRo) { lastRo = roKey; const box = document.getElementById('ro'); box.replaceChildren(); ro.forEach(([a, b]) => { const row = document.createElement('div'); row.className = 'readout'; const l = document.createElement('span'), s = document.createElement('strong'); l.textContent = a; s.textContent = b; row.append(l, s); box.append(row); }); }
    const fx = cfg.formula(S, M); if (fx !== lastFx) { lastFx = fx; document.getElementById('fx').textContent = fx; }
    const tx = cfg.logic(S, M); if (tx !== lastTx) { lastTx = tx; document.getElementById('takeaway').textContent = tx; }
    watch();
    requestAnimationFrame(frame);
  }
  fit(); restart(); sync(); resetChange(); requestAnimationFrame(frame);
  window.addEventListener('message', e => { if (e.data && e.data.type === 'jeenius-params') { const q = e.data.params || {}; controls.forEach(c => { if (q[c.key] !== undefined && !isNaN(+q[c.key])) S[c.key] = clamp(+q[c.key], c.min ?? 0, c.max ?? (c.options ? c.options.length - 1 : 1)); }); restart(); sync(); } });
  setInterval(() => { sync(); }, 250);
};
})();
