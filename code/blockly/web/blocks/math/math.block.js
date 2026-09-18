// ╔══════════════════════════════════════════════╗
// ║ Math blocks — arithmetic, constants, trig     ║
// ║ Ported 100% from PyCreator                     ║
// ╚══════════════════════════════════════════════╝

// ─── Number (built-in) ───
Blockly.Python['math_number'] = function(block) {
  var num = block.getFieldValue('NUM');
  return [num, Blockly.Python.ORDER_ATOMIC];
};

// ─── Arithmetic (built-in) ───
Blockly.Python['math_arithmetic'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_ATOMIC) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_ATOMIC) || '0';
  var pyOp, precedence;
  switch (op) {
    case 'ADD':      pyOp = '+';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
    case 'MINUS':    pyOp = '-';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
    case 'MULTIPLY': pyOp = '*';  precedence = Blockly.Python.ORDER_MULTIPLICATIVE; break;
    case 'DIVIDE':   pyOp = '/';  precedence = Blockly.Python.ORDER_MULTIPLICATIVE; break;
    case 'POWER':    pyOp = '**'; precedence = Blockly.Python.ORDER_EXPONENTIATION; break;
    default:         pyOp = '+';  precedence = Blockly.Python.ORDER_ADDITIVE; break;
  }
  return [a + ' ' + pyOp + ' ' + b, precedence];
};

// ─── Modulo (custom) ───
Blockly.Blocks['me_modulo'] = {
  init: function() {
    this.appendValueInput("A").setCheck("Number").appendField("");
    this.appendDummyInput().appendField("mod");
    this.appendValueInput("B").setCheck("Number").appendField("");
    this.setInputsInline(true);
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Modulo (remainder) operation");
  }
};
Blockly.Python['me_modulo'] = function(block) {
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_MULTIPLICATIVE) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_MULTIPLICATIVE) || '1';
  return [a + ' % ' + b, Blockly.Python.ORDER_MULTIPLICATIVE];
};

// ─── Single function (built-in: sqrt, abs, neg, etc.) ───
Blockly.Python['math_single'] = function(block) {
  var op = block.getFieldValue('OP');
  var arg = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';
  var code;
  switch (op) {
    case 'ROOT':   code = 'math.sqrt(' + arg + ')'; break;
    case 'ABS':    code = 'abs(' + arg + ')'; break;
    case 'NEG':    code = '-' + arg; break;
    case 'LN':     code = 'math.log(' + arg + ')'; break;
    case 'LOG10':  code = 'math.log10(' + arg + ')'; break;
    case 'EXP':    code = 'math.exp(' + arg + ')'; break;
    case 'ROUND':  code = 'round(' + arg + ')'; break;
    case 'ROUNDUP':code = 'math.ceil(' + arg + ')'; break;
    case 'ROUNDDOWN':code = 'math.floor(' + arg + ')'; break;
    default:       code = arg; break;
  }
  var order = (op === 'NEG') ? Blockly.Python.ORDER_UNARY : Blockly.Python.ORDER_FUNCTION_CALL;
  return [code, order];
};

// ─── Trig (built-in) ───
Blockly.Python['math_trig'] = function(block) {
  var op = block.getFieldValue('OP');
  var arg = Blockly.Python.valueToCode(block, 'NUM', Blockly.Python.ORDER_NONE) || '0';
  var fn = {SIN:'sin',COS:'cos',TAN:'tan',ASIN:'asin',ACOS:'acos',ATAN:'atan'}[op] || 'sin';
  return ['math.' + fn + '(' + arg + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Constant (built-in) ───
Blockly.Python['math_constant'] = function(block) {
  var c = block.getFieldValue('CONSTANT');
  var val = {PI:'math.pi',E:'math.e',GOLDEN_RATIO:'(1 + 5 ** 0.5) / 2',SQRT2:'math.sqrt(2)'}[c] || '0';
  return [val, Blockly.Python.ORDER_ATOMIC];
};

// ─── Constrain (custom) ───
Blockly.Blocks['me_constrain'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck("Number").appendField("constrain");
    this.appendValueInput("LOW").setCheck("Number").appendField("min");
    this.appendValueInput("HIGH").setCheck("Number").appendField("max");
    this.setInputsInline(true);
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Clamp a value between min and max");
  }
};
Blockly.Python['me_constrain'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  var low = Blockly.Python.valueToCode(block, 'LOW', Blockly.Python.ORDER_NONE) || '0';
  var high = Blockly.Python.valueToCode(block, 'HIGH', Blockly.Python.ORDER_NONE) || '0';
  return ['max(' + low + ', min(' + val + ', ' + high + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Min / Max (custom) ───
Blockly.Blocks['me_min_max'] = {
  init: function() {
    this.appendValueInput("A").setCheck("Number");
    this.appendDummyInput().appendField(new Blockly.FieldDropdown([
      ["min", "min"], ["max", "max"]
    ]), "OP");
    this.appendValueInput("B").setCheck("Number");
    this.setInputsInline(true);
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Minimum or maximum of two values");
  }
};
Blockly.Python['me_min_max'] = function(block) {
  var op = block.getFieldValue('OP');
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_NONE) || '0';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_NONE) || '0';
  return [op + '(' + a + ', ' + b + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Random integer (custom) ───
Blockly.Blocks['me_random_int'] = {
  init: function() {
    this.appendDummyInput().appendField("random int from");
    this.appendValueInput("FROM").setCheck("Number");
    this.appendDummyInput().appendField("to");
    this.appendValueInput("TO").setCheck("Number");
    this.setInputsInline(true);
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Random integer between from and to (inclusive)");
  }
};
Blockly.Python['me_random_int'] = function(block) {
  var from = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_NONE) || '0';
  var to = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || '0';
  return ['random.randint(int(' + from + '), int(' + to + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Random float (custom) ───
Blockly.Blocks['me_random_float'] = {
  init: function() {
    this.appendDummyInput().appendField("random float from");
    this.appendValueInput("FROM").setCheck("Number");
    this.appendDummyInput().appendField("to");
    this.appendValueInput("TO").setCheck("Number");
    this.setInputsInline(true);
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Random float between from and to");
  }
};
Blockly.Python['me_random_float'] = function(block) {
  var from = Blockly.Python.valueToCode(block, 'FROM', Blockly.Python.ORDER_NONE) || '0';
  var to = Blockly.Python.valueToCode(block, 'TO', Blockly.Python.ORDER_NONE) || '1';
  return ['random.uniform(' + from + ', ' + to + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Round (custom) ───
Blockly.Blocks['me_round'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck("Number").appendField("round");
    this.setOutput(true, "Number");
    this.setColour(230);
    this.setTooltip("Round to nearest integer");
  }
};
Blockly.Python['me_round'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return ['round(' + val + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
