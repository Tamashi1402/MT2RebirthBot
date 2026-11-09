// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_func_def                           ║
// ║ Category: base/flow                           ║
// ║ Desc: Floating Function definition with       ║
// ║   unlimited parameters (mutator gear).        ║
// ║   Not connected to the procedure flow —       ║
// ║   like a void/module-level function.          ║
// ╚══════════════════════════════════════════════╝


// ─── Mutator constructor shim (Blockly v10 vs v11+) ───
// v11 removed the global Blockly.Mutator constructor and moved it to
// Blockly.icons.MutatorIcon. Support both so the blocks work on any bundle.
function _pcrMakeMutator(block, quarkNames) {
  if (Blockly.icons && Blockly.icons.MutatorIcon) {
    return new Blockly.icons.MutatorIcon(quarkNames, block);
  }
  return new Blockly.Mutator(quarkNames, block);
}

// ─── Shared parameter "quark" blocks ───
// Three DISTINCT block types (not one block with a type dropdown) so the
// mutator flyout looks and behaves like normal typed Blockly blocks —
// each with the colour of its matching category (same hues the app's
// own theme uses for text/math/logic blocks), not the Function block's
// green. Used inside BOTH the Function's "pass into function:" mutator
// and the Play function's "pass to function:" mutator.
var PCR_PARAM_BLOCK_BY_TYPE = {
  string: 'pcr_param_string',
  number: 'pcr_param_number',
  bool: 'pcr_param_bool'
};
var PCR_PARAM_TYPE_BY_BLOCK = {
  pcr_param_string: 'string',
  pcr_param_number: 'number',
  pcr_param_bool: 'bool'
};

function _pcrParamBlockType(type) {
  return PCR_PARAM_BLOCK_BY_TYPE[type] || 'pcr_param_string';
}

function _pcrParamType(blockType) {
  return PCR_PARAM_TYPE_BY_BLOCK[blockType] || 'string';
}

Blockly.Blocks['pcr_param_string'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('parameter string')
      .appendField(new Blockly.FieldTextInput('value'), 'PARAM_NAME');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160); // typical Blockly "text" hue
    this.contextMenu = false;
    this.setTooltip('A text (string) parameter. Type its name here.');
  }
};

Blockly.Blocks['pcr_param_number'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('Parameter number')
      .appendField(new Blockly.FieldTextInput('value'), 'PARAM_NAME');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(230); // typical Blockly "math" hue
    this.contextMenu = false;
    this.setTooltip('A number parameter. Type its name here.');
  }
};

Blockly.Blocks['pcr_param_bool'] = {
  init: function() {
    this.appendDummyInput()
      .appendField('parameter logic')
      .appendField(new Blockly.FieldTextInput('value'), 'PARAM_NAME');
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210); // typical Blockly "logic" hue
    this.contextMenu = false;
    this.setTooltip('A true/false (boolean) parameter. Type its name here.');
  }
};

// ─── Definition ───
Blockly.Blocks['pcr_func_def'] = {
  init: function() {
    this.appendDummyInput("HEADER")
      .appendField("Function")
      .appendField(new Blockly.FieldTextInput("my_function"), "NAME");
    this.appendStatementInput("DO").setCheck(null);
    this.params_ = [];
    this.setPreviousStatement(false);
    this.setNextStatement(false);
    this.setColour(120);
    this.setTooltip(
      "Define a function with parameters (add via the gear).\n" +
      "Floats freely — it does NOT need to be inside the main flow.\n" +
      "Run it from anywhere with the 'Play function' block.\n" +
      "Parameters appear as 'Param: <name>' in the get/set variable\n" +
      "dropdowns — use them inside this function's body."
    );
    this.setMutator(_pcrMakeMutator(this, ['pcr_param_string', 'pcr_param_number', 'pcr_param_bool']));
  },

  mutationToDom: function() {
    var container = document.createElement('mutation');
    container.setAttribute('params', this.params_.length);
    for (var i = 0; i < this.params_.length; i++) {
      var p = document.createElement('param');
      p.setAttribute('name', this.params_[i].name);
      p.setAttribute('type', this.params_[i].type);
      container.appendChild(p);
    }
    return container;
  },

  domToMutation: function(xmlElement) {
    this.params_ = [];
    var children = xmlElement.children || xmlElement.childNodes || [];
    for (var i = 0; i < children.length; i++) {
      var c = children[i];
      if (c.tagName && c.tagName.toLowerCase() === 'param') {
        this.params_.push({
          name: c.getAttribute('name') || 'value' + (i + 1),
          type: c.getAttribute('type') || 'string'
        });
      }
    }
    this.updateShape_();
  },

  decompose: function(workspace) {
    var container = workspace.newBlock('pcr_func_def_mutator');
    container.initSvg();
    var conn = container.getInput('STACK').connection;
    for (var i = 0; i < this.params_.length; i++) {
      var item = workspace.newBlock(_pcrParamBlockType(this.params_[i].type));
      item.setFieldValue(this.params_[i].name, 'PARAM_NAME');
      item.initSvg();
      item.render();
      conn.connect(item.previousConnection);
      conn = item.nextConnection;
    }
    return container;
  },

  compose: function(containerBlock) {
    var params = [];
    var item = containerBlock.getInputTargetBlock('STACK');
    while (item) {
      params.push({
        name: item.getFieldValue('PARAM_NAME'),
        type: _pcrParamType(item.type)
      });
      item = item.nextConnection && item.nextConnection.targetBlock();
    }
    this.params_ = params;
    this.updateShape_();
  },

  saveConnections: function() { /* params have no value connections on the def */ },

  updateShape_: function() {
    // Preserve the body chain while rebuilding the rows.
    var bodyBlock = null;
    var doInput = this.getInput('DO');
    if (doInput && doInput.connection.targetBlock()) {
      bodyBlock = doInput.connection.targetBlock();
    }
    for (var i = this.inputList.length - 1; i >= 0; i--) {
      if (this.inputList[i].name !== 'HEADER') {
        this.removeInput(this.inputList[i].name);
      }
    }
    for (var i = 0; i < this.params_.length; i++) {
      var p = this.params_[i];
      // No socket needed here — defining a parameter is just a name + a
      // type, it never plugs into anything. Sockets only appear on the
      // "Play function" (call) side, where actual values are passed in.
      this.appendDummyInput('PARAM' + i)
        .appendField('    ' + p.name + ':', 'PLABEL' + i)
        .appendField(new Blockly.FieldLabel(p.type), 'PTYPE' + i);
    }
    this.appendStatementInput('DO').setCheck(null);
    if (bodyBlock) {
      var newDo = this.getInput('DO');
      if (newDo) {
        try { newDo.connection.connect(bodyBlock.previousConnection); } catch (e) {}
      }
    }
    if (this.rendered) {
      this.render();
    }
  }
};

// Mutator container — "pass into function:"
Blockly.Blocks['pcr_func_def_mutator'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("pass into function:");
    this.appendStatementInput("STACK");
    this.setColour(120);
    this.contextMenu = false;
    this.setTooltip("Drag in a parameter string / Parameter number / parameter logic block for each value the function should accept, then type its name.");
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_func_def'] = function(block) {
  var name = (block.getFieldValue('NAME') || 'my_function').trim();
  var fn = 'func_' + name.replace(/[^A-Za-z0-9_]/g, '_').replace(/^([0-9])/, '_$1');
  var params = block.params_ || [];
  var seen = {};
  var paramList = [];
  for (var i = 0; i < params.length; i++) {
    var pn = (params[i].name || 'value').trim().replace(/[^A-Za-z0-9_]/g, '_').replace(/^([0-9])/, '_$1');
    if (seen[pn]) {
      var k = 2;
      while (seen[pn + '_' + k]) k++;
      pn = pn + '_' + k;
    }
    seen[pn] = true;
    paramList.push(pn);
  }
  var body = Blockly.Python.statementToCode(block, 'DO');
  if (!body) {
    body = Blockly.Python.INDENT + 'pass\n';
  }
  // Sentinel markers let the codegen hoist this def to MODULE level so it
  // is callable from every procedure, not just the one it floats in.
  return '#@@PCR_FUNC_DEF@@\n'
    + 'def ' + fn + '(' + paramList.join(', ') + '):\n'
    + body
    + '#@@PCR_FUNC_DEF_END@@\n';
};

// Macro Forge: same block as mf_func_def (procedure dropdown + live registry).
if (Blockly.Blocks.mf_func_def) {
  Blockly.Blocks['pcr_func_def'] = Blockly.Blocks.mf_func_def;
  Blockly.Python['pcr_func_def'] = Blockly.Python.mf_func_def;
}
