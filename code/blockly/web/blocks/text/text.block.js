// ╔══════════════════════════════════════════════╗
// ║ Text blocks — string manipulation              ║
// ║ Ported 100% from PyCreator                     ║
// ╚══════════════════════════════════════════════╝

// ─── String literal (built-in) ───
Blockly.Python['text'] = function(block) {
  var text = block.getFieldValue('TEXT');
  return [JSON.stringify(text), Blockly.Python.ORDER_ATOMIC];
};

// ─── Text length (built-in) ───
Blockly.Python['text_length'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return ['len(' + text + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Text is empty (built-in) ───
Blockly.Python['text_isEmpty'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return ['len(' + text + ') == 0', Blockly.Python.ORDER_RELATIONAL];
};

// ─── Text append (built-in) ───
Blockly.Python['text_append'] = function(block) {
  var varName = Blockly.Python.variableDB_.getName(block.getFieldValue('VAR'), Blockly.VARIABLE_CATEGORY_NAME);
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return varName + ' = str(' + varName + ') + str(' + text + ')\n';
};

// ─── Text concat / join (built-in) ───
Blockly.Python['text_join'] = function(block) {
  var elements = [];
  for (var i = 0; i < block.itemCount_; i++) {
    var code = Blockly.Python.valueToCode(block, 'ADD' + i, Blockly.Python.ORDER_NONE) || "''";
    elements.push(code);
  }
  if (elements.length === 0) return ["''", Blockly.Python.ORDER_ATOMIC];
  if (elements.length === 1) return ['str(' + elements[0] + ')', Blockly.Python.ORDER_FUNCTION_CALL];
  var code = 'str(' + elements[0] + ')';
  for (var j = 1; j < elements.length; j++) { code += ' + str(' + elements[j] + ')'; }
  return [code, Blockly.Python.ORDER_ADDITION];
};

// ─── Change case (built-in) ───
Blockly.Python['text_changeCase'] = function(block) {
  var op = block.getFieldValue('CASE');
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  if (op === 'UPPERCASE') { return [text + '.upper()', Blockly.Python.ORDER_FUNCTION_CALL]; }
  return [text + '.lower()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Char at (built-in) ───
Blockly.Python['text_charAt'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_MEMBER) || "''";
  var at = Blockly.Python.valueToCode(block, 'AT', Blockly.Python.ORDER_NONE) || '0';
  return [text + '[' + at + ']', Blockly.Python.ORDER_MEMBER];
};

// ─── Substring / slice (built-in) ───
Blockly.Python['text_getSubstring'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || "''";
  var where1 = block.getFieldValue('WHERE1');
  var where2 = block.getFieldValue('WHERE2');
  var at1 = Blockly.Python.valueToCode(block, 'AT1', Blockly.Python.ORDER_NONE) || '0';
  var at2 = Blockly.Python.valueToCode(block, 'AT2', Blockly.Python.ORDER_NONE) || '0';
  var start, end;
  switch (where1) {
    case 'FROM_START': start = at1; break;
    case 'FROM_END':   start = '-' + at1; break;
    case 'FIRST':      start = '0'; break;
    default:           start = at1; break;
  }
  switch (where2) {
    case 'FROM_START': end = '(int(' + at2 + ') + 1)'; break;
    case 'FROM_END':   end = '-' + at2; break;
    case 'LAST':       end = ''; break;
    default:           end = at2; break;
  }
  return [text + '[' + start + ':' + end + ']', Blockly.Python.ORDER_MEMBER];
};

// ─── Index of (built-in) ───
Blockly.Python['text_indexOf'] = function(block) {
  var op = block.getFieldValue('END');
  var text = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  var sub = Blockly.Python.valueToCode(block, 'FIND', Blockly.Python.ORDER_NONE) || "''";
  if (op === 'FIRST') { return [text + '.find(' + sub + ')', Blockly.Python.ORDER_FUNCTION_CALL]; }
  return [text + '.rfind(' + sub + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Print (custom) ───
Blockly.Blocks['me_print'] = {
  init: function() {
    this.appendValueInput("TEXT").setCheck(null).appendField("print");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(160);
    this.setTooltip("Print to console");
  }
};
Blockly.Python['me_print'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'print(' + text + ')\n';
};

// ─── Contains (custom) ───
Blockly.Blocks['me_text_contains'] = {
  init: function() {
    this.appendValueInput("STRING").setCheck("String").appendField("");
    this.appendValueInput("SUB").setCheck("String").appendField("contains");
    this.setInputsInline(true);
    this.setOutput(true, "Boolean");
    this.setColour(210);
    this.setTooltip("Check if a string contains a substring");
  }
};
Blockly.Python['me_text_contains'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_NONE) || "''";
  var sub = Blockly.Python.valueToCode(block, 'SUB', Blockly.Python.ORDER_NONE) || "''";
  return [sub + ' in ' + str, Blockly.Python.ORDER_MEMBER];
};

// ─── Replace (custom) ───
Blockly.Blocks['me_text_replace'] = {
  init: function() {
    this.appendValueInput("STRING").setCheck("String").appendField("in");
    this.appendValueInput("OLD").setCheck("String").appendField("replace");
    this.appendValueInput("NEW").setCheck("String").appendField("with");
    this.setInputsInline(true);
    this.setOutput(true, "String");
    this.setColour(160);
    this.setTooltip("Replace all occurrences of old with new in a string");
  }
};
Blockly.Python['me_text_replace'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || "''";
  var old = Blockly.Python.valueToCode(block, 'OLD', Blockly.Python.ORDER_NONE) || "''";
  var nw = Blockly.Python.valueToCode(block, 'NEW', Blockly.Python.ORDER_NONE) || "''";
  return [str + '.replace(' + old + ', ' + nw + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Split (custom) ───
Blockly.Blocks['me_text_split'] = {
  init: function() {
    this.appendValueInput("STRING").setCheck("String").appendField("split");
    this.appendValueInput("SEP").setCheck("String").appendField("by");
    this.setInputsInline(true);
    this.setOutput(true, "Array");
    this.setColour(260);
    this.setTooltip("Split a string into a list by a separator");
  }
};
Blockly.Python['me_text_split'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || "''";
  var sep = Blockly.Python.valueToCode(block, 'SEP', Blockly.Python.ORDER_NONE) || "' '";
  return [str + '.split(' + sep + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Trim (custom) ───
Blockly.Blocks['me_text_trim'] = {
  init: function() {
    this.appendValueInput("VALUE").setCheck("String").appendField("trim");
    this.setOutput(true, "String");
    this.setColour(160);
    this.setTooltip("Remove leading and trailing whitespace");
  }
};
Blockly.Python['me_text_trim'] = function(block) {
  var val = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_MEMBER) || "''";
  return [val + '.strip()', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Format string (custom) ───
Blockly.Blocks['me_text_format'] = {
  init: function() {
    this.appendValueInput("TEMPLATE").setCheck("String").appendField("format");
    this.appendValueInput("VALUES").setCheck("Array").appendField("with");
    this.setInputsInline(true);
    this.setOutput(true, "String");
    this.setColour(160);
    this.setTooltip("Format a string template with a list of values");
  }
};
Blockly.Python['me_text_format'] = function(block) {
  var template = Blockly.Python.valueToCode(block, 'TEMPLATE', Blockly.Python.ORDER_NONE) || "''";
  var values = Blockly.Python.valueToCode(block, 'VALUES', Blockly.Python.ORDER_NONE) || '[]';
  return [template + '.format(*' + values + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

// ─── Input (custom) ───
Blockly.Blocks['me_text_input'] = {
  init: function() {
    this.appendValueInput("PROMPT").setCheck("String").appendField("input");
    this.setOutput(true, "String");
    this.setColour(160);
    this.setTooltip("Get user input from console (blocking)");
  }
};
Blockly.Python['me_text_input'] = function(block) {
  var prompt = Blockly.Python.valueToCode(block, 'PROMPT', Blockly.Python.ORDER_NONE) || "''";
  return ['input(' + prompt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
