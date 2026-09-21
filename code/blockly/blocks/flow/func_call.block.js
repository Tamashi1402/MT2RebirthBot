// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_func_call                          ║
// ║ Category: base/flow                           ║
// ║ Desc: Play/call a Function with arguments     ║
// ║   (mutator gear adds what to pass).           ║
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

// pcr_param_string / pcr_param_number / pcr_param_bool and their
// _pcrParamBlockType()/_pcrParamType() helpers are defined once in
// func_def.block.js and shared here (both files load into the same
// Blockly.Blocks registry).

// ─── Definition ───
Blockly.Blocks['pcr_func_call'] = {
  init: function() {
    this.appendDummyInput("HEADER")
      .appendField("Play function")
      .appendField(new Blockly.FieldTextInput("my_function"), "NAME");
    this.args_ = [];
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip(
      "Call a Function by name and pass values to its parameters (add them via the gear — same names/types as the Function block)."
    );
    this.setMutator(_pcrMakeMutator(this, ['pcr_param_string', 'pcr_param_number', 'pcr_param_bool']));
  },

  mutationToDom: function() {
    var container = document.createElement('mutation');
    container.setAttribute('args', this.args_.length);
    for (var i = 0; i < this.args_.length; i++) {
      var a = document.createElement('arg');
      a.setAttribute('name', this.args_[i].name);
      a.setAttribute('type', this.args_[i].type);
      container.appendChild(a);
    }
    return container;
  },

  domToMutation: function(xmlElement) {
    this.args_ = [];
    var children = xmlElement.children || xmlElement.childNodes || [];
    for (var i = 0; i < children.length; i++) {
      var c = children[i];
      if (c.tagName && c.tagName.toLowerCase() === 'arg') {
        this.args_.push({
          name: c.getAttribute('name') || 'value' + (i + 1),
          type: c.getAttribute('type') || 'string'
        });
      }
    }
    this.updateShape_();
  },

  decompose: function(workspace) {
    var container = workspace.newBlock('pcr_func_call_mutator');
    container.initSvg();
    var conn = container.getInput('STACK').connection;
    for (var i = 0; i < this.args_.length; i++) {
      var item = workspace.newBlock(_pcrParamBlockType(this.args_[i].type));
      item.setFieldValue(this.args_[i].name, 'PARAM_NAME');
      item.initSvg();
      item.render();
      conn.connect(item.previousConnection);
      conn = item.nextConnection;
    }
    return container;
  },

  compose: function(containerBlock) {
    var args = [];
    var item = containerBlock.getInputTargetBlock('STACK');
    while (item) {
      args.push({
        name: item.getFieldValue('PARAM_NAME'),
        type: _pcrParamType(item.type)
      });
      item = item.nextConnection && item.nextConnection.targetBlock();
    }
    this.args_ = args;
    this.updateShape_();
  },

  saveConnections: function() { /* handled inline in updateShape_ */ },

  updateShape_: function() {
    // Preserve already-connected argument blocks across the rebuild —
    // reconnect by POSITION so a value survives a pure rename/type-swap
    // of the same slot (previously this only reconnected on an exact
    // type match, which is why editing a parameter often silently
    // dropped whatever was plugged into it).
    var oldValues = [];
    for (var i = 0; i < this.args_.length; i++) {
      var inp = this.getInput('ARG' + i);
      oldValues.push(inp && inp.connection ? inp.connection.targetBlock() : null);
    }
    for (var i = this.inputList.length - 1; i >= 0; i--) {
      if (this.inputList[i].name !== 'HEADER') {
        this.removeInput(this.inputList[i].name);
      }
    }
    for (var i = 0; i < this.args_.length; i++) {
      var a = this.args_[i];
      // Real, open value socket — no type check, so ANY block (text,
      // number, logic, variable, expression...) can be plugged in here.
      // This is the ONLY place a socket appears; parameters on the
      // Function definition itself never get one.
      this.appendValueInput('ARG' + i)
        .appendField(a.name + ' (' + a.type + '):', 'ALABEL' + i);
    }
    for (var i = 0; i < this.args_.length && i < oldValues.length; i++) {
      if (oldValues[i]) {
        var newInput = this.getInput('ARG' + i);
        if (newInput) {
          try { newInput.connection.connect(oldValues[i].outputConnection); } catch (e) {}
        }
      }
    }
    if (this.rendered) {
      this.render();
    }
  }
};

// Mutator container — "pass to function:"
Blockly.Blocks['pcr_func_call_mutator'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("pass to function:");
    this.appendStatementInput("STACK");
    this.setColour(120);
    this.contextMenu = false;
    this.setTooltip("Drag in a parameter string / Parameter number / parameter logic block for each value to pass — same names as the Function's parameters — then plug a value into it on the main block.");
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_func_call'] = function(block) {
  var name = (block.getFieldValue('NAME') || 'my_function').trim();
  var fn = 'func_' + name.replace(/[^A-Za-z0-9_]/g, '_').replace(/^([0-9])/, '_$1');
  var args = block.args_ || [];
  var parts = [];
  var seen = {};
  for (var i = 0; i < args.length; i++) {
    var an = (args[i].name || 'value').trim().replace(/[^A-Za-z0-9_]/g, '_').replace(/^([0-9])/, '_$1');
    if (seen[an]) {
      var k = 2;
      while (seen[an + '_' + k]) k++;
      an = an + '_' + k;
    }
    seen[an] = true;
    var fallback = 'None';
    if (args[i].type === 'number') fallback = '0';
    else if (args[i].type === 'bool') fallback = 'False';
    var val = Blockly.Python.valueToCode(block, 'ARG' + i, Blockly.Python.ORDER_NONE);
    if (val === '' || val === null || val === undefined) val = fallback;
    parts.push(an + '=' + val);
  }
  return fn + '(' + parts.join(', ') + ')\n';
};

// Macro Forge: cascading procedure → function droplists, auto arg sockets.
if (Blockly.Blocks.mf_func_call) {
  Blockly.Blocks['pcr_func_call'] = Blockly.Blocks.mf_func_call;
  Blockly.Python['pcr_func_call'] = Blockly.Python.mf_func_call;
}
