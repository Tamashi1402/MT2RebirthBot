// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_text_split                           ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Split string by delimiter               ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_text_split'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_text_split",
      "message0": "Split %1 by %2",
      "args0": [
        { "type": "input_value", "name": "STRING", "check": "String" },
        { "type": "input_value", "name": "DELIM", "check": "String" }
      ],
      "inputsInline": true,
      "output": "Array",
      "colour": 260,
      "tooltip": "Split a string into a list by a delimiter"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_text_split'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_NONE) || "''";
  var delim = Blockly.Python.valueToCode(block, 'DELIM', Blockly.Python.ORDER_NONE) || "' '";
  return [str + '.split(' + delim + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
