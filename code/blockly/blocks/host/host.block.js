function mt2Menu(key, fallback) {
  return function () {
    var list = window[key];
    if (list && list.length) return list;
    return fallback;
  };
}

Blockly.Blocks['host_run_should_stop'] = {
  init: function() {
    this.appendDummyInput().appendField("run.should_stop");
    this.setOutput(true, "Boolean");
    this.setColour(20);
    this.setTooltip("Engine kill switch. True after Stop / F9 / fail.");
  }
};
Blockly.Python['host_run_should_stop'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.run.should_stop")', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_run_elapsed'] = {
  init: function() {
    this.appendDummyInput().appendField("run.elapsed");
    this.setOutput(true, "Number");
    this.setColour(20);
  }
};
Blockly.Python['host_run_elapsed'] = function() {
  return ['macroforge.engine.functions.call("macroforge.engine.run.elapsed")', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_run_fail'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("run.fail")
      .appendField(new Blockly.FieldTextInput("reason"), "REASON");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(0);
  }
};
Blockly.Python['host_run_fail'] = function(block) {
  return 'macroforge.engine.functions.call("macroforge.engine.run.fail", ' + JSON.stringify(block.getFieldValue('REASON')) + ')\n';
};

Blockly.Blocks['host_overlay_set'] = {
  init: function() {
    this.appendValueInput("VALUE")
      .appendField("Set overlay")
      .appendField(new Blockly.FieldDropdown([["header","header"],["name","name"]]), "SLOT")
      .appendField("to");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160);
    this.setTooltip("Push a value into the overlay compositor. Slots come from this addon.");
  }
};
Blockly.Python['host_overlay_set'] = function(block) {
  var slot = JSON.stringify(block.getFieldValue('SLOT'));
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '""';
  return 'macroforge.engine.functions.call("macroforge.engine.overlay.set", ' + slot + ', ' + value + ')\n';
};

Blockly.Blocks['host_stats_record'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("stats.record")
      .appendField(new Blockly.FieldTextInput("event"), "EVENT");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(260);
  }
};
Blockly.Python['host_stats_record'] = function(block) {
  return 'macroforge.engine.functions.call("macroforge.engine.stats.record", ' + JSON.stringify(block.getFieldValue('EVENT')) + ')\n';
};

Blockly.Blocks['host_stats_query'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("stats.query")
      .appendField(new Blockly.FieldTextInput("event"), "EVENT");
    this.setOutput(true, null);
    this.setColour(260);
  }
};
Blockly.Python['host_stats_query'] = function(block) {
  var code = 'macroforge.engine.stats.get(' + JSON.stringify(block.getFieldValue('EVENT')) + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_log_info'] = {
  init: function() {
    this.appendValueInput("MSG").setCheck("String").appendField("log.info");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
  }
};
Blockly.Python['host_log_info'] = function(block) {
  var msg = Blockly.Python.valueToCode(block, 'MSG', Blockly.Python.ORDER_NONE) || '""';
  return 'macroforge.engine.functions.call("macroforge.engine.log.info", ' + msg + ')\n';
};

Blockly.Blocks['host_call_function'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call function")
      .appendField(new Blockly.FieldDropdown(mt2Menu("__MT2_FNS", [["macroforge.engine.macro.play", "macroforge.engine.macro.play"]])), "FN");
    this.appendValueInput("ARG0").appendField("arg");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210);
    this.setTooltip("Call a registered host or addon function by id. No game nouns in the toolbox.");
  }
};
Blockly.Python['host_call_function'] = function(block) {
  var fn = block.getFieldValue('FN');
  if (fn && fn.indexOf('host.') === 0) fn = 'macroforge.engine.' + fn.slice(5);
  else if (fn && fn.indexOf('engine.') === 0 && fn.indexOf('macroforge.engine.') !== 0) fn = 'macroforge.engine.' + fn.slice(7);  // legacy id → macroforge.engine id
  fn = JSON.stringify(fn);
  var arg = Blockly.Python.valueToCode(block, 'ARG0', Blockly.Python.ORDER_NONE);
  var call = arg ? 'macroforge.engine.functions.call(' + fn + ', ' + arg + ')' : 'macroforge.engine.functions.call(' + fn + ')';
  return call + '\n';
};

Blockly.Blocks['host_call_value'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call function")
      .appendField(new Blockly.FieldDropdown(mt2Menu("__MT2_FNS", [["macroforge.engine.config.get", "macroforge.engine.config.get"]])), "FN");
    this.appendValueInput("ARG0").appendField("arg");
    this.setOutput(true, null);
    this.setColour(210);
    this.setTooltip("Call a function and use its return (conditions, stats, dashboard binds).");
  }
};
Blockly.Python['host_call_value'] = function(block) {
  var fn = block.getFieldValue('FN');
  if (fn && fn.indexOf('host.') === 0) fn = 'macroforge.engine.' + fn.slice(5);
  else if (fn && fn.indexOf('engine.') === 0 && fn.indexOf('macroforge.engine.') !== 0) fn = 'macroforge.engine.' + fn.slice(7);  // legacy id → macroforge.engine id
  fn = JSON.stringify(fn);
  var arg = Blockly.Python.valueToCode(block, 'ARG0', Blockly.Python.ORDER_NONE);
  var call = arg ? 'macroforge.engine.functions.call(' + fn + ', ' + arg + ')' : 'macroforge.engine.functions.call(' + fn + ')';
  return [call, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_json_get'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("config.get")
      .appendField(new Blockly.FieldTextInput("rebirths_done"), "KEY");
    this.setOutput(true, null);
    this.setColour(60);
    this.setTooltip("Read a value from the addon's data json (e.g. tracker file).");
  }
};
Blockly.Python['host_json_get'] = function(block) {
  var code = 'macroforge.engine.config.get(' + JSON.stringify(block.getFieldValue('KEY')) + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['host_return_value'] = {
  init: function() {
    this.appendValueInput("VALUE").appendField("return");
    this.setPreviousStatement(true, null);
    this.setColour(120);
    this.setTooltip("Return a value from this procedure (dashboard binds / edge conditions).");
  }
};
Blockly.Python['host_return_value'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return 'return ' + value + '\n';
};
