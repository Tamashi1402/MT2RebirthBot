// ╔══════════════════════════════════════════════╗
// ║ Variables blocks — type-specific get/set       ║
// ║ Separate blocks per type (not generic)         ║
// ║ Ported from PyCreator's typed_get/typed_set    ║
// ╚══════════════════════════════════════════════╝

// ─── Type → Blockly colour mapping ───
var ME_VAR_COLOURS = {
  text: 160,
  number: 230,
  logic: 210,
  list: 260
};

// ─── Helper: build dropdown options for a given type ───
function meVarDropdownOptions(varType) {
  var options = [];
  var globalVars = window._meGlobalVars || {};
  for (var name in globalVars) {
    if (globalVars[name] === varType) {
      options.push(["Global: " + name, name]);
    }
  }
  var localVars = window._meLocalVars || {};
  for (var name2 in localVars) {
    if (localVars[name2] === varType) {
      options.push(["Local: " + name2, name2]);
    }
  }
  if (options.length === 0) {
    options.push(["(no variables of this type)", ""]);
  }
  return options;
}

// ─── GET TEXT ───
Blockly.Blocks['me_get_text'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("get text")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('text'); }), "VAR");
    this.setOutput(true, null);
    this.setColour(160);
    this.setTooltip("Get the value of a text variable");
  }
};
Blockly.Python['me_get_text'] = function(block) {
  var v = block.getFieldValue('VAR');
  return [v || 'None', Blockly.Python.ORDER_ATOMIC];
};

// ─── GET NUMBER ───
Blockly.Blocks['me_get_number'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("get number")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('number'); }), "VAR");
    this.setOutput(true, null);
    this.setColour(230);
    this.setTooltip("Get the value of a number variable");
  }
};
Blockly.Python['me_get_number'] = function(block) {
  var v = block.getFieldValue('VAR');
  return [v || '0', Blockly.Python.ORDER_ATOMIC];
};

// ─── GET LOGIC ───
Blockly.Blocks['me_get_logic'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("get logic")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('logic'); }), "VAR");
    this.setOutput(true, null);
    this.setColour(210);
    this.setTooltip("Get the value of a boolean variable");
  }
};
Blockly.Python['me_get_logic'] = function(block) {
  var v = block.getFieldValue('VAR');
  return [v || 'False', Blockly.Python.ORDER_ATOMIC];
};

// ─── GET LIST ───
Blockly.Blocks['me_get_list'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("get list")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('list'); }), "VAR");
    this.setOutput(true, null);
    this.setColour(260);
    this.setTooltip("Get the value of a list variable");
  }
};
Blockly.Python['me_get_list'] = function(block) {
  var v = block.getFieldValue('VAR');
  return [v || '[]', Blockly.Python.ORDER_ATOMIC];
};

// ─── SET TEXT ───
Blockly.Blocks['me_set_text'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("set text")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('text'); }), "VAR");
    this.appendValueInput("VALUE").setCheck(null).setAlign(Blockly.ALIGN_RIGHT).appendField("to");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(160);
    this.setTooltip("Set a text variable to a new value");
  }
};
Blockly.Python['me_set_text'] = function(block) {
  var v = block.getFieldValue('VAR');
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return v + ' = ' + val + '\n';
};

// ─── SET NUMBER ───
Blockly.Blocks['me_set_number'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("set number")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('number'); }), "VAR");
    this.appendValueInput("VALUE").setCheck(null).setAlign(Blockly.ALIGN_RIGHT).appendField("to");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(230);
    this.setTooltip("Set a number variable to a new value");
  }
};
Blockly.Python['me_set_number'] = function(block) {
  var v = block.getFieldValue('VAR');
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return v + ' = ' + val + '\n';
};

// ─── SET LOGIC ───
Blockly.Blocks['me_set_logic'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("set logic")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('logic'); }), "VAR");
    this.appendValueInput("VALUE").setCheck(null).setAlign(Blockly.ALIGN_RIGHT).appendField("to");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip("Set a boolean variable to a new value");
  }
};
Blockly.Python['me_set_logic'] = function(block) {
  var v = block.getFieldValue('VAR');
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'False';
  return v + ' = ' + val + '\n';
};

// ─── SET LIST ───
Blockly.Blocks['me_set_list'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("set list")
      .appendField(new Blockly.FieldDropdown(function() { return meVarDropdownOptions('list'); }), "VAR");
    this.appendValueInput("VALUE").setCheck(null).setAlign(Blockly.ALIGN_RIGHT).appendField("to");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setInputsInline(true);
    this.setColour(260);
    this.setTooltip("Set a list variable to a new value");
  }
};
Blockly.Python['me_set_list'] = function(block) {
  var v = block.getFieldValue('VAR');
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '[]';
  return v + ' = ' + val + '\n';
};


