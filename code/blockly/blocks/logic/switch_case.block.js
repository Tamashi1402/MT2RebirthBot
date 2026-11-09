// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_switch                             ║
// ║ Category: base/logic                          ║
// ║ Desc: Switch/case — compares one "switch"     ║
// ║   value against each case's value (in order)  ║
// ║   and runs the first match's "do". Add more   ║
// ║   cases (and an optional "default" fallback)  ║
// ║   via the gear \u2699, same mutator pattern as    ║
// ║   the if / else if / else block.               ║
// ╚══════════════════════════════════════════════╝
//
// Shape:
//   switch [data]
//     case [value]        <- CASE0 / DO0, always present (like IF0/DO0
//       do [ ... ]            on the if block — not removable via the gear)
//     case [value]         <- extra cases, added via the gear (like "else if")
//       do [ ... ]
//     default               <- optional, added via the gear (like "else"),
//       do [ ... ]              always sits last
//
// Python: the switch expression is evaluated ONCE into a temp variable
// (so an expression with side effects, e.g. a function call, only runs
// once no matter how many cases you add), then compared with == against
// each case value top-to-bottom as if/elif/.../else — first match wins.

// ─── Mutator constructor shim (Blockly v10 vs v11+) ───
// (Same helper as flow/func_def.block.js / flow/while.block.js — flow/
// loads before logic/ alphabetically, but redeclare defensively so this
// file also works standalone.)
function _pcrMakeMutator(block, quarkNames) {
  if (Blockly.icons && Blockly.icons.MutatorIcon) {
    return new Blockly.icons.MutatorIcon(quarkNames, block);
  }
  return new Blockly.Mutator(quarkNames, block);
}

// reconnect a saved connection to a freshly (re)created input, if both exist
function _pcrSwitchReconnect(conn, block, inputName) {
  var input = block.getInput(inputName);
  if (!input || !conn) return;
  try { conn.reconnect(input.connection); } catch (e) {
    try { input.connection.connect(conn); } catch (e2) {}
  }
}

Blockly.Blocks['pcr_switch'] = {
  init: function () {
    this.appendValueInput('SWITCH').appendField('switch');
    this.appendValueInput('CASE0').appendField('case');
    this.appendStatementInput('DO0').appendField('do');
    this.setInputsInline(false);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210); // Logic hue
    this.caseCount_ = 0;   // EXTRA cases beyond the always-present CASE0/DO0
    this.hasDefault_ = false;
    this.setTooltip(
      'Compares \u201cswitch\u201d against each case value (top to bottom) and runs ' +
      'the first match\u2019s \u201cdo\u201d \u2014 like a chain of if/elif. Click the gear ' +
      '\u2699 to add more cases, and optionally a \u201cdefault\u201d branch that runs ' +
      'when nothing matched (drag it in last, like \u2018else\u2019 on the if block). ' +
      'The switch value is evaluated once no matter how many cases you add.'
    );
    this.setMutator(_pcrMakeMutator(this, ['pcr_switch_case_item', 'pcr_switch_default_item']));
  },

  mutationToDom: function () {
    var container = document.createElement('mutation');
    container.setAttribute('cases', this.caseCount_);
    if (this.hasDefault_) container.setAttribute('default', '1');
    return container;
  },

  domToMutation: function (xmlElement) {
    this.caseCount_ = parseInt(xmlElement.getAttribute('cases'), 10) || 0;
    this.hasDefault_ = xmlElement.getAttribute('default') === '1';
    this.updateShape_();
  },

  decompose: function (workspace) {
    var container = workspace.newBlock('pcr_switch_mutator');
    container.initSvg();
    var connection = container.getInput('STACK').connection;
    for (var i = 0; i < this.caseCount_; i++) {
      var caseItem = workspace.newBlock('pcr_switch_case_item');
      caseItem.initSvg();
      connection.connect(caseItem.previousConnection);
      connection = caseItem.nextConnection;
    }
    if (this.hasDefault_) {
      var defaultItem = workspace.newBlock('pcr_switch_default_item');
      defaultItem.initSvg();
      connection.connect(defaultItem.previousConnection);
    }
    return container;
  },

  compose: function (containerBlock) {
    var clauseBlock = containerBlock.getInputTargetBlock('STACK');
    var caseCount = 0;
    var hasDefault = false;
    var valueConnections = [null];       // [0] unused — CASE0 is never touched
    var statementConnections = [null];   // [0] unused — DO0 is never touched
    var defaultConnection = null;
    while (clauseBlock) {
      if (clauseBlock.type === 'pcr_switch_case_item') {
        caseCount++;
        valueConnections.push(clauseBlock.mfValueConn_ || null);
        statementConnections.push(clauseBlock.mfStatementConn_ || null);
      } else if (clauseBlock.type === 'pcr_switch_default_item') {
        hasDefault = true;
        defaultConnection = clauseBlock.mfStatementConn_ || null;
      }
      clauseBlock = clauseBlock.nextConnection && clauseBlock.nextConnection.targetBlock();
    }
    this.caseCount_ = caseCount;
    this.hasDefault_ = hasDefault;
    this.updateShape_();
    for (var i = 1; i <= caseCount; i++) {
      _pcrSwitchReconnect(valueConnections[i], this, 'CASE' + i);
      _pcrSwitchReconnect(statementConnections[i], this, 'DO' + i);
    }
    if (hasDefault) {
      _pcrSwitchReconnect(defaultConnection, this, 'DEFAULT');
    }
  },

  saveConnections: function (containerBlock) {
    // Walk the (possibly reordered) quark chain in parallel with this
    // block's numbered inputs, stashing each connected child block's
    // connection ON the quark item itself — compose() reads it back
    // after rebuilding the rows, so drag-reordering in the gear popup
    // never drops a case's value/body.
    var clauseBlock = containerBlock.getInputTargetBlock('STACK');
    var i = 1;
    while (clauseBlock) {
      if (clauseBlock.type === 'pcr_switch_case_item') {
        var inputCase = this.getInput('CASE' + i);
        var inputDo = this.getInput('DO' + i);
        clauseBlock.mfValueConn_ = inputCase && inputCase.connection.targetConnection;
        clauseBlock.mfStatementConn_ = inputDo && inputDo.connection.targetConnection;
        i++;
      } else if (clauseBlock.type === 'pcr_switch_default_item') {
        var inputDefault = this.getInput('DEFAULT');
        clauseBlock.mfStatementConn_ = inputDefault && inputDefault.connection.targetConnection;
      }
      clauseBlock = clauseBlock.nextConnection && clauseBlock.nextConnection.targetBlock();
    }
  },

  updateShape_: function () {
    // SWITCH / CASE0 / DO0 are never touched — exactly like the if
    // block's IF0/DO0, they're not part of the mutator and always keep
    // whatever is plugged into them.
    for (var idx = this.inputList.length - 1; idx >= 0; idx--) {
      var name = this.inputList[idx].name;
      if (name !== 'SWITCH' && name !== 'CASE0' && name !== 'DO0') {
        this.removeInput(name);
      }
    }
    for (var i = 1; i <= this.caseCount_; i++) {
      this.appendValueInput('CASE' + i).appendField('case');
      this.appendStatementInput('DO' + i).appendField('do');
    }
    if (this.hasDefault_) {
      this.appendStatementInput('DEFAULT').appendField('default');
    }
    if (this.rendered) {
      this.render();
    }
  },
};

// Mutator container — "switch cases:" popup header
Blockly.Blocks['pcr_switch_mutator'] = {
  init: function () {
    this.appendDummyInput().appendField('switch cases:');
    this.appendStatementInput('STACK');
    this.setColour(210);
    this.contextMenu = false;
    this.setTooltip(
      'Drag in a \u201ccase\u201d block for each extra value to check, and \u2014 ' +
      'optionally, last \u2014 one \u201cdefault\u201d block for a fallback that runs ' +
      'when nothing else matched.'
    );
  },
};

// Quark: one more "case" row (value + do) — the mutator equivalent of
// "else if". Unlimited, reorderable, always before "default".
Blockly.Blocks['pcr_switch_case_item'] = {
  init: function () {
    this.appendDummyInput().appendField('case');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210);
    this.contextMenu = false;
    this.setTooltip('One more case: a value to compare against \u201cswitch\u201d, and a \u201cdo\u201d body that runs when it matches.');
  },
};

// Quark: the "default" fallback row — the mutator equivalent of "else".
// No next-connection, so (like "else") it can never have another quark
// dragged after it — it's structurally always last.
Blockly.Blocks['pcr_switch_default_item'] = {
  init: function () {
    this.appendDummyInput().appendField('default');
    this.setPreviousStatement(true, null);
    this.setColour(210);
    this.contextMenu = false;
    this.setTooltip('A fallback body that runs when no case matched \u2014 like \u201celse\u201d on the if block. Always last.');
  },
};

// ─── Python Generator ───
// Build the condition for one case input. An "or" block plugged into a
// case ("a5 or area5") distributes the comparison — _switch == 'a5' or
// _switch == 'area5' — instead of the old output which was
// _switch == 'a5' or 'area5' (a truthy string, so it matched EVERYTHING
// and every unmatched value fell into that branch).
function _pcrSwitchCaseCond(varName, block, inputName) {
  var b = block.getInputTargetBlock ? block.getInputTargetBlock(inputName) : null;
  if (b && b.type === 'logic_operation' && (b.getFieldValue('OP') || 'OR').toUpperCase() === 'OR') {
    var a = _pcrSwitchCaseCond(varName, b, 'A');
    var c = _pcrSwitchCaseCond(varName, b, 'B');
    return a + ' or ' + c;
  }
  var v = Blockly.Python.valueToCode(block, inputName, Blockly.Python.ORDER_NONE) || 'None';
  return varName + ' == ' + v;
}

Blockly.Python['pcr_switch'] = function (block) {
  var switchExpr = Blockly.Python.valueToCode(block, 'SWITCH', Blockly.Python.ORDER_NONE) || 'None';
  // Evaluate the switch value exactly once, even with many cases —
  // matters if it's a call with side effects (e.g. reading input).
  var varName = '_switch_' + String(block.id || '').replace(/[^A-Za-z0-9_]/g, '_');
  if (!varName || varName === '_switch_') varName = '_switch_v';
  var code = varName + ' = ' + switchExpr + '\n';

  var n = 0;
  var wroteBranch = false;
  while (block.getInput('CASE' + n)) {
    var cond = _pcrSwitchCaseCond(varName, block, 'CASE' + n);
    var branch = Blockly.Python.statementToCode(block, 'DO' + n) || (Blockly.Python.INDENT + 'pass\n');
    code += (wroteBranch ? 'elif ' : 'if ') + cond + ':\n' + branch;
    wroteBranch = true;
    n++;
  }

  if (block.getInput('DEFAULT')) {
    var defaultBranch = Blockly.Python.statementToCode(block, 'DEFAULT') || (Blockly.Python.INDENT + 'pass\n');
    code += wroteBranch ? ('else:\n' + defaultBranch) : defaultBranch;
  }

  return code + '\n';
};
