// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_text_format                          ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Format string (f-string)                ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_text_format'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_text_format",
      "message0": "Format %1 with %2",
      "args0": [
        { "type": "input_value", "name": "TEMPLATE", "check": "String" },
        { "type": "input_value", "name": "VALUES", "check": "Array" }
      ],
      "inputsInline": true,
      "output": "String",
      "colour": 160,
      "tooltip": "Format a string template with a list of values"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_text_format'] = function(block) {
  var template = Blockly.Python.valueToCode(block, 'TEMPLATE', Blockly.Python.ORDER_NONE) || "''";
  var values = Blockly.Python.valueToCode(block, 'VALUES', Blockly.Python.ORDER_NONE) || '[]';
  // Python: template.format(*values)
  return [template + '.format(*' + values + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
