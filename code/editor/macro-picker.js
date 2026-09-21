// ═════════════════════════════════════════════════════════════════════════════
// MacroForge macro editor — pickers, 1:1 with the procedures editor's flows
//   window.MFPicker.requestPick(block, mode) — the API the editor's own
//     MFPickIcon buttons call. Modes:
//       'point'     → F2 screenshot → click a pixel → fills the point block
//       'res_image' → F2 screenshot → drag a box → crop is saved into the
//                     macro images dir and wired into pcr_image_from_res
//       'file'      → server file dialog → resource path text
//       'color'     → not used on the macro canvas (toast)
//   window.MfmPick.request(block, 'smooth') — hold-F2 movement capture for
//     the scaled-move block (same math as the recorder's L-hold).
// ═════════════════════════════════════════════════════════════════════════════
(function () {
  'use strict';

  // ── clickable label field (proven pattern from mf-plugins makeMappedField) ──
  function MfmPickField(kind) {
    var label = kind === 'smooth' ? '⌖ capture (hold F2)' : '⌖ pick (F2)';
    var field = new Blockly.FieldLabel(label);
    field.kind_ = kind;
    field.EDITABLE = true;
    field.SERIALIZABLE = false;
    field.showEditor_ = function () {
      if (window.MfmPick) window.MfmPick.request(this.sourceBlock_, this.kind_);
    };
    return field;
  }
  window.MfmPickField = MfmPickField;

  // ── value helpers on the editor's block types ─────────────────────────────
  function setNumInput(pt, name, v) {
    var inp = pt.getInput(name);
    var t = inp && inp.connection ? inp.connection.targetBlock() : null;
    if (t && (t.type === 'math_number' || t.isShadow())) {
      t.setFieldValue(String(v), 'NUM');
    } else {
      var n = pt.workspace.newBlock('math_number');
      n.setFieldValue(String(v), 'NUM');
      try { n.initSvg(); } catch (e) {}
      if (t) { try { t.dispose(); } catch (e) {} }
      if (inp.connection) n.outputConnection.connect(inp.connection);
    }
  }

  // write x,y into a pcr_point_xy wired to the given socket (create if missing)
  function setPointOn(block, inputName, x, y) {
    var input = block.getInput(inputName);
    if (!input || !input.connection) return false;
    var pt = input.connection.targetBlock();
    if (!pt || pt.type !== 'pcr_point_xy') {
      if (pt) { try { pt.dispose(); } catch (e) {} }
      pt = block.workspace.newBlock('pcr_point_xy');
      try { pt.initSvg(); } catch (e) {}
      setNumInput(pt, 'X', x);
      setNumInput(pt, 'Y', y);
      pt.outputConnection.connect(input.connection);
    } else {
      setNumInput(pt, 'X', x);
      setNumInput(pt, 'Y', y);
    }
    try { pt.initSvg(); pt.render(); block.render(); block.bumpNeighbours(); } catch (e) {}
    return true;
  }

  // write a text into a value socket of a block (creates a text block)
  function setTextOn(block, inputName, text) {
    var input = block.getInput(inputName);
    if (!input || !input.connection) return false;
    var t = input.connection.targetBlock();
    if (t && t.type === 'text') {
      t.setFieldValue(String(text), 'TEXT');
    } else {
      if (t) { try { t.dispose(); } catch (e) {} }
      var n = block.workspace.newBlock('text');
      n.setFieldValue(String(text), 'TEXT');
      try { n.initSvg(); } catch (e) {}
      n.outputConnection.connect(input.connection);
    }
    try { block.render(); block.bumpNeighbours(); } catch (e) {}
    return true;
  }

  // ── shared popup shell ──────────────────────────────────────────────────────
  var active = null; // {kind, block, poll, mode, onAccept}

  function ensurePopupRoot() {
    var root = document.getElementById('mfm-pop');
    if (root) return root;
    root = document.createElement('div');
    root.id = 'mfm-pop';
    root.innerHTML = '<div class="mfm-pop-panel">'
      + '<h3 id="mfm-pop-title"></h3>'
      + '<p id="mfm-pop-text"></p>'
      + '<div class="mfm-pop-status" id="mfm-pop-status"></div>'
      + '<button id="mfm-pop-cancel">Cancel</button>'
      + '</div>';
    document.body.appendChild(root);
    // the cancel button used to have NO handler — popups could never be
    // dismissed once armed ("won't go away now lol")
    root.querySelector('#mfm-pop-cancel').onclick = function () { closeAll(true); };
    return root;
  }

  function statusLine(text, ok) {
    var el = document.getElementById('mfm-pop-status');
    if (!el) return;
    el.textContent = text || '';
    el.className = 'mfm-pop-status' + (ok ? ' ok' : ' err');
  }

  function closeAll(disarm) {
    if (!active) return;
    if (active.poll) clearInterval(active.poll);
    var root = document.getElementById('mfm-pop');
    if (root) root.style.display = 'none';
    var ov = document.getElementById('mfm-shot');
    if (ov) ov.remove();
    active = null;
    if (disarm) {
      try { navigator.sendBeacon('/blockly/picker/cancel', '{}'); } catch (e) {}
      try { navigator.sendBeacon('/me/api/smooth_pick/cancel', '{}'); } catch (e) {}
    }
  }

  function toast(text) {
    var t = document.createElement('div');
    t.id = 'mfm-toast';
    t.textContent = text;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 2600);
  }

  window.addEventListener('pagehide', function () {
    try { navigator.sendBeacon('/blockly/picker/cancel', '{}'); } catch (e) {}
    try { navigator.sendBeacon('/me/api/smooth_pick/cancel', '{}'); } catch (e) {}
  });

  // ── F2 screenshot flow (point + box share it) ──────────────────────────────
  function armF2(onShot) {
    var root = ensurePopupRoot();
    root.style.display = 'flex';
    statusLine('Arming F2 …');

    fetch('/blockly/picker/prepare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: active.mode === 'box' ? 'box' : 'point' }),
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (!active) return;
      if (!d.ok) { statusLine('Error: ' + (d.error || 'could not arm F2'), false); return; }
      statusLine('Waiting for F2 … press it in your app', true);
    }).catch(function () { statusLine('Server unreachable', false); });

    active.poll = setInterval(function () {
      if (!active) return;
      fetch('/blockly/picker/status').then(function (r) { return r.json(); }).then(function (d) {
        if (!active) return;
        if (d.state === 'armed') statusLine('Waiting for F2 … press it in your app', true);
        else if (d.state === 'capturing') statusLine('Taking screenshot …', true);
        else if (d.state === 'captured' && d.has_shot) {
          clearInterval(active.poll); active.poll = null;
          onShot('/blockly/picker/shot?v=' + Date.now());
        } else if (d.state === 'error') {
          statusLine('Error: ' + (d.error || 'unknown'), false);
        }
      }).catch(function () {});
    }, 350);
  }

  // ── shot editor: click a pixel (point) or drag a rectangle (box) ───────────
  function openShotEditor(shotUrl) {
    var root = document.getElementById('mfm-pop');
    if (root) root.style.display = 'none';
    var isBox = active.mode === 'box';

    var ov = document.createElement('div');
    ov.id = 'mfm-shot';
    ov.innerHTML = '<img id="mfm-shot-img" alt="screenshot">'
      + '<div class="mfm-shot-bar">'
      + '<span class="mfm-hint">' + (isBox ? 'Drag a rectangle' : 'Click a pixel') + '</span>'
      + '<span class="mfm-coords" id="mfm-shot-coords"></span>'
      + '<button id="mfm-shot-cancel">Cancel</button>'
      + '<button id="mfm-shot-ok" class="primary">Accept</button>'
      + '</div>';
    document.body.appendChild(ov);

    var img = ov.querySelector('#mfm-shot-img');
    var map = { x: 0, y: 0, scale: 1 };
    var picked = null;   // point: [x,y]  box: [x1,y1,x2,y2]
    var dragStart = null;

    img.addEventListener('load', function () {
      var w = img.naturalWidth, h = img.naturalHeight;
      if (!w || !h) return;
      var availW = window.innerWidth, availH = window.innerHeight - 44;
      var scale = Math.min(availW / w, availH / h, 1);
      img.style.width = (w * scale) + 'px';
      img.style.height = (h * scale) + 'px';
      img.style.left = ((availW - w * scale) / 2) + 'px';
      img.style.top = ((availH - h * scale) / 2) + 'px';
      map = { x: (availW - w * scale) / 2, y: (availH - h * scale) / 2, scale: scale };
    });
    img.src = shotUrl;

    var sel = document.createElement('div');
    sel.id = 'mfm-shot-sel';
    ov.appendChild(sel);

    function toImg(e) {
      return [Math.round((e.clientX - map.x) / map.scale), Math.round((e.clientY - map.y) / map.scale)];
    }
    function drawSel(x1, y1, x2, y2) {
      sel.style.display = 'block';
      sel.style.left = (map.x + Math.min(x1, x2) * map.scale - 1) + 'px';
      sel.style.top = (map.y + Math.min(y1, y2) * map.scale - 1) + 'px';
      sel.style.width = (Math.abs(x2 - x1) * map.scale + 3) + 'px';
      sel.style.height = (Math.abs(y2 - y1) * map.scale + 3) + 'px';
    }

    if (!isBox) {
      ov.addEventListener('mousedown', function (e) {
        if (e.target.closest('.mfm-shot-bar')) return;
        e.preventDefault();
        picked = toImg(e);
        drawSel(picked[0], picked[1], picked[0], picked[1]);
        document.getElementById('mfm-shot-coords').textContent = '(' + picked[0] + ', ' + picked[1] + ')';
      });
    } else {
      ov.addEventListener('mousedown', function (e) {
        if (e.target.closest('.mfm-shot-bar')) return;
        e.preventDefault();
        dragStart = toImg(e);
        picked = null;
      });
      ov.addEventListener('mousemove', function (e) {
        if (!dragStart) return;
        var p = toImg(e);
        drawSel(dragStart[0], dragStart[1], p[0], p[1]);
        picked = [dragStart[0], dragStart[1], p[0], p[1]];
        document.getElementById('mfm-shot-coords').textContent =
          Math.abs(p[0] - dragStart[0]) + ' × ' + Math.abs(p[1] - dragStart[1]);
      });
      ov.addEventListener('mouseup', function () {
        if (dragStart && picked) {
          var x1 = Math.min(picked[0], picked[2]), x2 = Math.max(picked[0], picked[2]);
          var y1 = Math.min(picked[1], picked[3]), y2 = Math.max(picked[1], picked[3]);
          picked = [x1, y1, x2, y2];
          dragStart = null;
        } else { dragStart = null; }
      });
    }

    ov.querySelector('#mfm-shot-cancel').onclick = function () { closeAll(true); };
    ov.querySelector('#mfm-shot-ok').onclick = function () {
      if (!picked || (isBox && (picked[2] - picked[0] < 1 || picked[3] - picked[1] < 1))) {
        toast(isBox ? 'Drag a rectangle first' : 'Click a pixel first');
        return;
      }
      var cb = active.onAccept;
      var kind = active.kind;
      if (kind === 'point' || kind === 'box') { closeAll(true); cb(picked); return; }
      if (kind === 'color') {
        // sample BEFORE closeAll removes the overlay — the img is gone after
        var c = readShotPixel(picked[0], picked[1]);
        closeAll(true);
        cb(picked, c);
        return;
      }
      // res_image: the crop reads the screenshot SERVER-SIDE after we
      // return — closeAll(true) used to send the picker-cancel beacon
      // first, which deleted the shot ("no screenshot to crop"). Hide the
      // UI now; the accept fn disarms the picker once the crop is done.
      closeAll(false);
      cb(picked);
    };
  }

  // ── picker entry points ────────────────────────────────────────────────────

  // point → fill X/Y of the block (pcr_point_xy and friends)
  function pickPoint(block, onDone) {
    // create the popup shell FIRST — setting the title before the DOM
    // exists threw a TypeError mid-click, which aborted Blockly's pointer
    // handling and left the block glued to the cursor forever
    ensurePopupRoot();
    active = { kind: 'point', block: block, mode: 'point', onAccept: function (p) {
      if (block.getInput('POINT')) {
        // a socket block (scaled/abs move) → wire a pcr_point_xy in
        setPointOn(block, 'POINT', p[0], p[1]);
      } else {
        // a bare pcr_point_xy (its own crosshair icon) → set its X/Y
        setNumInput(block, 'X', p[0]);
        setNumInput(block, 'Y', p[1]);
        try { block.render(); block.bumpNeighbours(); } catch (e) {}
      }
      toast('Point set to (' + p[0] + ', ' + p[1] + ')');
      if (onDone) onDone();
    } };
    document.getElementById('mfm-pop-title').textContent = 'Pick a screen point';
    document.getElementById('mfm-pop-text').textContent =
      'Switch to your app, press F2 — a screenshot is taken instantly. ' +
      'Then click the pixel in the screenshot.';
    armF2(openShotEditor);
  }

  // res_image → drag a box → crop saved into the macro images dir → PATH
  function pickResImage(block, onDone) {
    ensurePopupRoot();   // same crash-to-glued-block bug as pickPoint (see above)
    active = { kind: 'res_image', block: block, mode: 'box', onAccept: function (box) {
      var disarm = function () {
        try { navigator.sendBeacon('/blockly/picker/cancel', '{}'); } catch (e) {}
      };
      // 1) ask the engine where images for this macro live
      fetch('/me/api/image_save_dir').then(function (r) { return r.json(); }).then(function (t) {
        if (!t.ok || !t.dir) { toast('Could not resolve the image folder'); disarm(); return; }
        // 2) crop on the DASHBOARD — it owns the F2 screenshot. Going
        //    through /me/api/crop_to_image made the engine import a fresh
        //    copy of the dashboard module whose picker state was always
        //    empty ("no screenshot to crop").
        return fetch('/blockly/picker/crop_to_file', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ box: box, dir: t.dir }),
        }).then(function (r) { return r.json(); }).then(function (d) {
          if (!d.ok) { toast(d.error || 'Crop failed'); }
          else {
            setTextOn(block, 'PATH', d.path);
            try { if (block.mfRefreshPreview) block.mfRefreshPreview(); } catch (e) {}
            toast('Image saved: ' + d.path);
            if (onDone) onDone();
          }
          disarm();
        });
      }).catch(function () {
        toast('Server unreachable');
        disarm();
      });
    } };
    document.getElementById('mfm-pop-title').textContent = 'Pick an image region';
    document.getElementById('mfm-pop-text').textContent =
      'Switch to your app, press F2 — a screenshot is taken instantly. ' +
      'Then drag the rectangle you want to find on screen. The crop is saved ' +
      'into the macro images folder and shown on the block.';
    armF2(openShotEditor);
  }

  // file → the ENGINE's native dialog (synchronous GET; returns the path)
  function pickFile(block, onDone) {
    ensurePopupRoot();
    active = { kind: 'file', block: block, mode: 'point', onAccept: null };
    var root = document.getElementById('mfm-pop');
    document.getElementById('mfm-pop-title').textContent = 'Choose a file';
    document.getElementById('mfm-pop-text').textContent =
      'The file dialog opens on the machine running MacroForge. Pick the file.';
    statusLine('Opening file dialog \u2026');
    root.style.display = 'flex';
    fetch('/me/api/dialog/open').then(function (r) { return r.json(); }).then(function (d) {
      if (!active) return;
      if (d && d.ok && d.path) {
        setTextOn(block, 'PATH', d.path);
        toast('Path set: ' + d.path);
        if (onDone) onDone();
      } else if (d && d.cancelled) {
        toast('Cancelled');
      } else {
        toast('Could not open the file dialog');
      }
      closeAll(true);
    }).catch(function () {
      if (!active) return;
      statusLine('Server unreachable', false);
    });
  }

  // ── get-image block → drag a rectangle → fill POINT (top-left) + SIZE ──
  // (the size box keeps X1/Y1 at 0 — width = X2, height = Y2)
  function setGrabSizeOn(block, inputName, w, h) {
    var input = block.getInput(inputName);
    if (!input || !input.connection) return false;
    var bx = input.connection.targetBlock();
    if (!bx || bx.type !== 'pcr_box_xyxy') {
      if (bx) { try { bx.dispose(); } catch (e) {} }
      bx = block.workspace.newBlock('pcr_box_xyxy');
      try { bx.initSvg(); } catch (e) {}
      bx.outputConnection.connect(input.connection);
    }
    setNumInput(bx, 'X1', 0);
    setNumInput(bx, 'Y1', 0);
    setNumInput(bx, 'X2', w);
    setNumInput(bx, 'Y2', h);
    return true;
  }

  function pickGrab(block) {
    ensurePopupRoot();
    active = { kind: 'box', block: block, mode: 'box', onAccept: function (b) {
      setPointOn(block, 'POINT', b[0], b[1]);
      setGrabSizeOn(block, 'SIZE', b[2] - b[0], b[3] - b[1]);
      try { block.render(); block.bumpNeighbours(); } catch (e) {}
      toast('Grab set: point (' + b[0] + ', ' + b[1] + '), size ' + (b[2] - b[0]) + 'x' + (b[3] - b[1]));
    } };
    document.getElementById('mfm-pop-title').textContent = 'Pick a screen region';
    document.getElementById('mfm-pop-text').textContent =
      'Switch to your app, press F2 — a screenshot is taken instantly. ' +
      'Then drag the rectangle you want to grab.';
    armF2(openShotEditor);
  }

  // the API the editor's MFPickIcon buttons call (1:1 contract).
  // mf-plugins dispatches by mode: point → MFPicker.requestPick,
  // res_image → MFResImage.request, file → MFFileDialog.request,
  // color → MFColorPick.request.
  window.MFResImage = {
    request: function (block) { return pickResImage(block); },
  };
  window.MFFileDialog = {
    request: function (block) { return pickFile(block); },
  };
  // ── box → drag a rectangle → fill X1/Y1/X2/Y2 of the box block ──────────
  function pickBox(block) {
    ensurePopupRoot();
    active = { kind: 'box', block: block, mode: 'box', onAccept: function (b) {
      setNumInput(block, 'X1', b[0]);
      setNumInput(block, 'Y1', b[1]);
      setNumInput(block, 'X2', b[2]);
      setNumInput(block, 'Y2', b[3]);
      try { block.render(); block.bumpNeighbours(); } catch (e) {}
      toast('Region set to (' + b[0] + ', ' + b[1] + ') \u2013 (' + b[2] + ', ' + b[3] + ')');
    } };
    document.getElementById('mfm-pop-title').textContent = 'Pick a screen region';
    document.getElementById('mfm-pop-text').textContent =
      'Switch to your app, press F2 — a screenshot is taken instantly. ' +
      'Then drag the rectangle you want.';
    armF2(openShotEditor);
  }

  // ── color pipette (1:1 with the flow editor's MFColorPick) ─────────────
  function readShotPixel(x, y) {
    try {
      var img = document.getElementById('mfm-shot-img');
      if (!img || !img.naturalWidth) return null;
      var cv = document.createElement('canvas');
      cv.width = img.naturalWidth; cv.height = img.naturalHeight;
      var ctx = cv.getContext('2d');
      ctx.drawImage(img, 0, 0);
      var px = Math.max(0, Math.min(x, cv.width - 1));
      var py = Math.max(0, Math.min(y, cv.height - 1));
      var d = ctx.getImageData(px, py, 1, 1).data;
      return [d[0], d[1], d[2]];
    } catch (e) { return null; }
  }

  function pickColor(block) {
    ensurePopupRoot();
    active = { kind: 'color', block: block, mode: 'point', onAccept: function (p, c) {
      if (!c) { toast('Could not read the pixel color'); return; }
      // the pipette icon lives on pcr_color_rgba — fill its R/G/B sockets
      setNumInput(block, 'R', c[0]);
      setNumInput(block, 'G', c[1]);
      setNumInput(block, 'B', c[2]);
      try { block.render(); block.bumpNeighbours(); } catch (e) {}
      var hex = '#' + c.map(function (v) { return ('0' + v.toString(16)).slice(-2); }).join('').toUpperCase();
      toast('Picked ' + hex + '  (R ' + c[0] + ' G ' + c[1] + ' B ' + c[2] + ')');
    } };
    document.getElementById('mfm-pop-title').textContent = 'Pick a color';
    document.getElementById('mfm-pop-text').textContent =
      'Switch to your app, press F2 — a screenshot is taken instantly. ' +
      'Then click the pixel whose color you want.';
    armF2(openShotEditor);
  }

  window.MFColorPick = {
    request: function (block) { return pickColor(block); },
  };
  window.MFPicker = {
    requestPick: function (block, mode) {
      if (mode === 'smooth') return pickSmooth(block);
      if (mode === 'point') return pickPoint(block);
      if (mode === 'res_image') return pickResImage(block);
      if (mode === 'file') return pickFile(block);
      if (mode === 'grab') { return pickGrab(block); }
      if (mode === 'box') { return pickBox(block); }
      toast('Unknown picker mode: ' + mode);
    },
  };

  // ── 'smooth': hold F2 → net movement (like the recorder's L-hold) ──────────
  function pickSmooth(block) {
    active = { kind: 'smooth', block: block, mode: 'point', onAccept: null };
    var root = ensurePopupRoot();
    document.getElementById('mfm-pop-title').textContent = 'Capture movement';
    document.getElementById('mfm-pop-text').textContent =
      'Hold F2 in your game and move the mouse (camera) — the net movement ' +
      'is captured when you release, scaled exactly like a recorded smooth move.';
    statusLine('Arming F2 …');
    root.style.display = 'flex';

    var baseSeq = 0;
    fetch('/me/api/smooth_pick/arm', { method: 'POST' }).then(function (r) { return r.json(); }).then(function (d) {
      if (!active) return;
      if (!d.ok) { statusLine('Could not arm F2 capture', false); return; }
      fetch('/me/api/smooth_pick/status').then(function (r) { return r.json(); }).then(function (s) {
        if (s && active) baseSeq = s.seq || 0;
      }).catch(function () {});
      statusLine('Hold F2 and move — release to capture', true);
    }).catch(function () { statusLine('Server unreachable', false); });

    active.poll = setInterval(function () {
      if (!active) return;
      fetch('/me/api/smooth_pick/status').then(function (r) { return r.json(); }).then(function (d) {
        if (!active) return;
        if ((d.seq || 0) > baseSeq) {
          var x = d.x || 0, y = d.y || 0;
          var ok = setPointOn(active.block, 'POINT', x, y);
          fetch('/me/api/smooth_pick/cancel', { method: 'POST' }).catch(function () {});
          closeAll(false);
          if (ok) toast('Movement captured: (' + x + ', ' + y + ')');
          else toast('Capture could not be applied');
        }
      }).catch(function () {});
    }, 350);
  }

  window.MfmPick = {
    request: function (block, kind) {
      if (kind === 'smooth') return pickSmooth(block);
      if (kind === 'point') return pickPoint(block);
      return pickSmooth(block);
    },
  };
})();
