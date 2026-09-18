// ╔══════════════════════════════════════════════╗
// ║ Logic blocks — if/else, comparisons, booleans ║
// ║ Ported 100% from PyCreator                     ║
// ╚══════════════════════════════════════════════╝

// ─── If / Else If / Else (built-in) ───
Blockly.Python['controls_if'] = function(block) {
  var code = '';
  var n = 0;
  var condition, branch;
  while (block.getInput('IF' + n)) {
    condition = Blockly.Python.valueToCode(block, 'IF' + n, Blockly.Python.ORDER_NONE) || 'False';
    branch = Blockly.Python.statementToCode(block, 'DO' + n) || '    pass\n';
    if (n === 0) { code = 'if ' + condition + ':\n' + branch; }
    else { code += 'elif ' + condition + ':\n' + branch; }
    n++;
  }
  if (block.getInput('ELSE')) {
    branch = Blockly.Python.statementToCode(block, 'ELSE') || '    pass\n';
    code += 'else:\n' + branch;
  }
  return code + '\n';
};

// ─── Comparison (built-in) ───
Blockly.Python['logic_compare'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_RELATIONAL) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_RELATIONAL) || '0';
  var pyOp = {EQ:'==',NEQ:'!=',LT:'<',LTE:'<=',GT:'>',GTE:'>='}[op] || '==';
  return [a + ' ' + pyOp + ' ' + b, Blockly.Python.ORDER_RELATIONAL];
};

// ─── And / Or (built-in) ───
Blockly.Python['logic_operation'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_LOGICAL_AND) || 'False';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_LOGICAL_AND) || 'False';
  var pyOp = (op === 'AND') ? 'and' : 'or';
  var order = (op === 'AND') ? Blockly.Python.ORDER_LOGICAL_AND : Blockly.Python.ORDER_LOGICAL_OR;
  return [a + ' ' + pyOp + ' ' + b, order];
};

// ─── Not (built-in) ───
Blockly.Python['logic_negate'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'BOOL', Blockly.Python.ORDER_LOGICAL_NOT) || 'False';
  return ['not ' + val, Blockly.Python.ORDER_LOGICAL_NOT];
};

// ─── True / False (built-in) ───
Blockly.Python['logic_boolean'] = function(block) {
  var val = block.getFieldValue('BOOL');
  return [(val === 'TRUE') ? 'True' : 'False', Blockly.Python.ORDER_ATOMIC];
};

// ─── Null / None (built-in) ───
Blockly.Python['logic_null'] = function(block) {
  return ['None', Blockly.Python.ORDER_ATOMIC];
};

// ─── Ternary (built-in) ───
Blockly.Python['logic_ternary'] = function(block) {
  var cond = Blockly.Python.valueToCode(block, 'IF', Blockly.Python.ORDER_CONDITIONAL) || 'False';
  var thenVal = Blockly.Python.valueToCode(block, 'THEN', Blockly.Python.ORDER_CONDITIONAL) || 'None';
  var elseVal = Blockly.Python.valueToCode(block, 'ELSE', Blockly.Python.ORDER_CONDITIONAL) || 'None';
  return ['(' + thenVal + ') if (' + cond + ') else (' + elseVal + ')', Blockly.Python.ORDER_CONDITIONAL];
};

// ─── Is None (custom) ───
Blockly.Blocks['me_is_none'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck(null).appendField("is none");
    this.setOutput(true, "Boolean");
    this.setColour(210);
    this.setTooltip("Check if a value is None");
  }
};
Blockly.Python['me_is_none'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return ['(' + val + ') is None', Blockly.Python.ORDER_LOGICAL_AND];
};

// ─── Is Not None (custom) ───
Blockly.Blocks['me_is_not_none'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck(null).appendField("is not none");
    this.setOutput(true, "Boolean");
    this.setColour(210);
    this.setTooltip("Check if a value is not None");
  }
};
Blockly.Python['me_is_not_none'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return ['(' + val + ') is not None', Blockly.Python.ORDER_LOGICAL_AND];
};

// ─── Try / Except (custom) ───
Blockly.Blocks['me_try_except'] = {
  init: function() {
    this.appendStatementInput("TRY").setCheck(null).appendField("try");
    this.appendStatementInput("CATCH").setCheck(null).appendField("except");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(210);
    this.setTooltip("Try a block of code, catch exceptions");
  }
};
Blockly.Python['me_try_except'] = function(block) {
  var tryCode = Blockly.Python.statementToCode(block, 'TRY') || '    pass\n';
  var catchCode = Blockly.Python.statementToCode(block, 'CATCH') || '    pass\n';
  var code = 'try:\n' + tryCode + 'except Exception:\n' + catchCode;
  return code;
};
