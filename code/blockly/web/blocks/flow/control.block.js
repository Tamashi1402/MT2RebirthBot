// ╔══════════════════════════════════════════════╗
// ║ Flow blocks — loops, returns, comments, calls ║
// ║ Ported 100% from PyCreator                     ║
// ╚══════════════════════════════════════════════╝

// ─── Break / Continue (built-in) ───
Blockly.Python['controls_flow_statements'] = function(block) {
  var type = block.getFieldValue('FLOW');
  if (type === 'BREAK') { return 'break\n'; }
  return 'continue\n';
};

// ─── While / Until (built-in) ───
Blockly.Python['controls_whileUntil'] = function(block) {
  var mode = block.getFieldValue('MODE');
  var condition = Blockly.Python.valueToCode(block, 'BOOL', Blockly.Python.ORDER_NONE) || 'False';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  if (mode === 'WHILE') { return 'while ' + condition + ':\n' + branch; }
  return 'while not ' + condition + ':\n' + branch;
};

// ─── Repeat N times (built-in) ───
Blockly.Python['controls_repeat_ext'] = function(block) {
  var times = Blockly.Python.valueToCode(block, 'TIMES', Blockly.Python.ORDER_NONE) || '0';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  return 'for _ in range(int(' + times + ')):\n' + branch;
};

// ─── For each (built-in) ───
Blockly.Python['controls_forEach'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_NONE) || '[]';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  return 'for ' + varName + ' in ' + list + ':\n' + branch;
};

// ─── For range (built-in) ───
Blockly.Python['controls_for'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var start = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_NONE) || '0';
  var end = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || '0';
  var step = Blockly.Python.valueToCode(block, 'BY', Blockly.Python.ORDER_NONE) || '1';
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  return 'for ' + varName + ' in range(' + start + ', ' + end + ', ' + step + '):\n' + branch;
};

// ─── Comment (custom) ───
Blockly.Blocks['me_comment'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck("String").appendField("#");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("A single-line Python comment (does not affect execution)");
  }
};
Blockly.Python['me_comment'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return '# ' + text + '\n';
};

// ─── While True (custom) ───
Blockly.Blocks['me_while_true'] = {
  init: function() {
    this.appendDummyInput().appendField("while true");
    this.appendStatementInput("DO").setCheck(null);
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Infinite loop — use break to exit");
  }
};
Blockly.Python['me_while_true'] = function(block) {
  var branch = Blockly.Python.statementToCode(block, 'DO') || '    pass\n';
  return 'while True:\n' + branch;
};

// ─── Procedure call (custom) ───
Blockly.Blocks['me_proc_call'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._meCallableProcs || [];
          if (procs.length === 0) return [["(no procedures)", ""]];
          return procs.map(function(p) { return [p, p]; });
        }
      ), "PROC_NAME");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Call another procedure by name");
  }
};
Blockly.Python['me_proc_call'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return 'pass\n';
  var fn = 'proc_' + name.replace(/ /g, '_').replace(/-/g, '_');
  return fn + '()\n';
};

// ─── Procedure call with return value (custom) ───
Blockly.Blocks['me_proc_call_return'] = {
  init: function() {
    this.appendDummyInput()
      .appendField("call and get")
      .appendField(new Blockly.FieldDropdown(
        function() {
          var procs = window._meCallableProcs || [];
          if (procs.length === 0) return [["(no procedures)", ""]];
          return procs.map(function(p) { return [p, p]; });
        }
      ), "PROC_NAME");
    this.setOutput(true, null);
    this.setColour(120);
    this.setTooltip("Call a procedure and get its return value");
  }
};
Blockly.Python['me_proc_call_return'] = function(block) {
  var name = block.getFieldValue('PROC_NAME');
  if (!name) return ['None', Blockly.Python.ORDER_ATOMIC];
  var fn = 'proc_' + name.replace(/ /g, '_').replace(/-/g, '_');
  return [fn + '()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Return none (custom) ───
Blockly.Blocks['me_return_none'] = {
  init: function() {
    this.appendDummyInput().appendField("return");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Return from this procedure without a value");
  }
};
Blockly.Python['me_return_none'] = function(block) { return 'return\n'; };

// ─── Return value (custom) ───
Blockly.Blocks['me_return_text'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck(null).appendField("return");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160);
    this.setTooltip("Return a value from this procedure");
  }
};
Blockly.Python['me_return_text'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return "return " + val + "\n";
};

// ─── Return value (custom) ───
Blockly.Blocks['me_return_value'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck(null).appendField("return");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Return a value from this procedure");
  }
};
Blockly.Python['me_return_value'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return 'return ' + value + '\n';
};
