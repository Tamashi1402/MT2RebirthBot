// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_text_replace                         ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Replace substring                       ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_text_replace'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_text_replace",
      "message0": "In %1 replace %2 with %3",
      "args0": [
        { "type": "input_value", "name": "STRING", "check": "String" },
        { "type": "input_value", "name": "OLD", "check": "String" },
        { "type": "input_value", "name": "NEW", "check": "String" }
      ],
      "inputsInline": true,
      "output": "String",
      "colour": 160,
      "tooltip": "Replace all occurrences of a substring"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_text_replace'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_NONE) || "''";
  var old_str = Blockly.Python.valueToCode(block, 'OLD', Blockly.Python.ORDER_NONE) || "''";
  var new_str = Blockly.Python.valueToCode(block, 'NEW', Blockly.Python.ORDER_NONE) || "''";
  return [str + '.replace(' + old_str + ', ' + new_str + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
