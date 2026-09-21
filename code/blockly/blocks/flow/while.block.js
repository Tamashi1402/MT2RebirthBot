// ╔══════════════════════════════════════════════╗
// ║ Block: controls_whileUntil                      ║
// ║ Category: base/flow                           ║
// ║ Built-in: Yes (extended with a mutator)       ║
// ║ Desc: While / Until loop, with an optional    ║
// ║       BACKGROUND arm (mutator gear)           ║
// ╚══════════════════════════════════════════════╝

// Repeat while/until — with an optional BACKGROUND arm bolted on via the
// mutator gear (same gear the IF block uses). A normal loop whose
// condition reads a variable the BACKGROUND arm keeps updated off-thread —
// the hot body never pays grab/decode cost:
//   repeat until (ready == 1) { ...hot clicks... } in background {
//     set ready = (img_diff(...) == 0)   // polled on a side thread
//     delay 100
//   }
// The arm runs repeatedly while the loop lives and stops the moment the
// loop exits. Click the gear, drag "background arm" in/out — just like
// dragging "else if" onto the IF block.
//
// This OVERRIDES Blockly's stock controls_whileUntil definition (loaded
// before this file) so there is exactly one repeat while/until block in
// the toolbox — no separate "with background" duplicate.
Blockly.Blocks['controls_whileUntil'] = {
  init: function () {
    // mutator gear — same icon the IF block uses. Modern Blockly (v10+,
    // this bundle) exposes it as Blockly.icons.MutatorIcon(quarkNames,
    // block) rather than the old Blockly.Mutator(quarkNames); constructor
    // takes the block itself as 2nd arg. Guarded for older/headless builds.
    if (Blockly.icons && typeof Blockly.icons.MutatorIcon === 'function') {
      this.setMutator(new Blockly.icons.MutatorIcon(['mfm_bg_item'], this));
    } else if (typeof Blockly.Mutator === 'function') {
      this.setMutator(new Blockly.Mutator(['mfm_bg_item']));
    }
    this.appendValueInput('BOOL')
      .setCheck('Boolean')
      .appendField(new Blockly.FieldDropdown([['repeat while', 'WHILE'], ['repeat until', 'UNTIL']]), 'MODE');
    this.appendStatementInput('DO').appendField('do');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip('While/until loop. Click the gear to add a background arm \u2014 its steps run on a background thread for as long as the loop lives (typically setting the variable this loop\u2019s condition reads; image checks cost nothing in the hot body) and stop the instant the loop exits.');
    this.mfmHasBg = false;
  },
  mutationToDom: function () {
    var m = document.createElement('mutation');
    m.setAttribute('hasbg', this.mfmHasBg ? '1' : '0');
    return m;
  },
  domToMutation: function (el) {
    this.mfmHasBg = (el.getAttribute('hasbg') === '1');
    this.mfmRenderBg();
  },
  mfmRenderBg: function () {
    if (this.mfmHasBg && !this.getInput('BACKGROUND')) {
      this.appendStatementInput('BACKGROUND').appendField('in background');
    } else if (!this.mfmHasBg && this.getInput('BACKGROUND')) {
      var held = this.getInputTargetBlock('BACKGROUND');
      if (held) { held.unplug(); held.bumpNeighbours(); }
      this.removeInput('BACKGROUND');
    }
  },
  decompose: function (ws) {
    var c = ws.newBlock('mfm_while_bg_container');
    c.initSvg();
    if (this.mfmHasBg) {
      var item = ws.newBlock('mfm_bg_item');
      item.initSvg();
      c.getInput('STACK').connection.connect(item.previousConnection);
    }
    return c;
  },
  compose: function (c) {
    var item = c.getInputTargetBlock('STACK');
    var has = !!item;
    if (has !== this.mfmHasBg) {
      this.mfmHasBg = has;
      this.mfmRenderBg();
    }
  },
};

// mutator bubble blocks — the gear popup contents. Same two helper blocks
// used before; they now belong to controls_whileUntil directly instead of
// a separate mfm_while_bg block.
Blockly.Blocks['mfm_while_bg_container'] = {
  init: function () {
    this.appendDummyInput().appendField('repeat while/until');
    this.appendStatementInput('STACK');
    this.setColour(120);
    this.setTooltip('Attach \'background\' to give this loop a background arm.');
    this.contextMenu = false;
  },
};
Blockly.Blocks['mfm_bg_item'] = {
  init: function () {
    this.appendDummyInput().appendField('background arm');
    this.setPreviousStatement(true, null);
    this.setColour(120);
    this.setTooltip('The loop\u2019s background arm: its steps run on a background thread while the loop lives.');
    this.contextMenu = false;
  },
};

// ─── Python Generator ───
Blockly.Python['controls_whileUntil'] = function (block) {
  var IND = Blockly.Python.INDENT || '    ';
  var mode = block.getFieldValue('MODE');
  var condition = Blockly.Python.valueToCode(block, 'BOOL', Blockly.Python.ORDER_NONE) || 'False';
  var branch = Blockly.Python.statementToCode(block, 'DO') || (IND + 'pass\n');
  var neg = (mode === 'WHILE') ? '' : 'not ';
  var stopCheck = IND + 'if stopped():\n' + IND + IND + 'break\n';

  if (!block.getInput('BACKGROUND')) {
    return 'while ' + neg + condition + ' and not stopped():\n' + stopCheck + branch;
  }

  var bg = Blockly.Python.statementToCode(block, 'BACKGROUND') || (IND + 'pass\n');
  var ind = function (src, pad) {
    var lines = src.split('\n');
    return lines.map(function (l, i) {
      return (i === lines.length - 1 && !l.trim()) ? l : pad + l;
    }).join('\n');
  };

  var assigned = {};
  var re = /\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:=(?!=)|\+=|-=|\*=|\/=|\/\/=|%=)/g;
  var KW = { if: 1, elif: 1, else: 1, while: 1, for: 1, return: 1, def: 1,
             global: 1, class: 1, with: 1, try: 1, except: 1, finally: 1,
             lambda: 1, del: 1, assert: 1, pass: 1, break: 1, continue: 1,
             import: 1, from: 1, as: 1, and: 1, or: 1, not: 1, in: 1, is: 1,
             print: 1 };
  var m;
  while ((m = re.exec(bg))) { if (!KW[m[1]]) assigned[m[1]] = 1; }
  var names = Object.keys(assigned).sort();

  Blockly.Python._mfmBgSeq = (Blockly.Python._mfmBgSeq || 0) + 1;
  var uid = 'bg' + Blockly.Python._mfmBgSeq;
  var evt = uid + '_done';
  var arm = uid + '_arm';
  var thr = uid + '_thread';

  var out = '';
  out += evt + ' = threading.Event()\n';
  out += 'def ' + arm + '():\n';
  if (names.length) out += IND + 'global ' + names.join(', ') + '\n';
  out += IND + 'try:\n';
  out += IND + IND + 'while not ' + evt + '.is_set() and not stopped():\n';
  out += ind(bg, IND + IND);
  out += IND + 'except Exception as _bg_err:\n';
  out += IND + IND + 'print("background arm error:", _bg_err)\n';
  out += thr + ' = threading.Thread(target=' + arm + ', daemon=True, name=' + JSON.stringify(uid) + ')\n';
  out += thr + '.start()\n';
  out += 'try:\n';
  out += IND + 'while ' + neg + condition + ' and not stopped():\n';
  out += ind(stopCheck + branch, IND);
  out += 'finally:\n';
  out += IND + evt + '.set()\n';
  out += IND + thr + '.join(timeout=1.0)\n';
  return out;
};
