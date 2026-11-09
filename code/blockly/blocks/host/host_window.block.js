// Host window primitives — engine, not game nouns
Blockly.Blocks['host_title_contains'] = {
  init: function() {
    this.appendValueInput('TEXT')
      .setCheck('String')
      .appendField("window title contains");
    this.setOutput(true, "Boolean");
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip("True if any window title contains the given text.");
  }
};
Blockly.Python['host_title_contains'] = function(block) {
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var code = 'macroforge.engine.functions.call("macroforge.engine.window.title_contains", ' + t + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_title_is_fullscreen'] = {
  init: function() {
    this.appendValueInput('TEXT')
      .setCheck('String')
      .appendField("window")
      .appendField("is fullscreen");
    this.setOutput(true, "Boolean");
    this.setInputsInline(true);
    this.setColour(210);
    this.setTooltip("True if the window whose title contains the given text is currently fullscreen.");
  }
};
Blockly.Python['host_title_is_fullscreen'] = function(block) {
  var t = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  var code = 'macroforge.engine.functions.call("macroforge.engine.window.is_fullscreen", ' + t + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_is_fullscreen'] = {
  init: function() {
    this.appendDummyInput().appendField("current window is fullscreen");
    this.setOutput(true, "Boolean");
    this.setColour(210);
  }
};
Blockly.Python['host_is_fullscreen'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.window.is_fullscreen")', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_wait_match'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("wait until window title contains")
      .appendField(new Blockly.FieldTextInput(""), "TEXT")
      .appendField("timeout")
      .appendField(new Blockly.FieldNumber(15, 1), "TIMEOUT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210);
  }
};
Blockly.Python['host_wait_match'] = function(block) {
  var t = block.getFieldValue('TEXT');
  var n = Number(block.getFieldValue('TIMEOUT'));
  return 'macroforge.engine.functions.call("macroforge.engine.window.wait_match", ' + JSON.stringify(t) + ', ' + n + ')\n';
};
