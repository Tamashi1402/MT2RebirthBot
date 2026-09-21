// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_is_not_none                          ║
// ║ Category: base/logic                          ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Check if value is not None             ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_is_not_none'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_is_not_none",
      "message0": "%1 is not None",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a value is not None"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_is_not_none'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || 'None';
  return [value + ' is not None', Blockly.Python.ORDER_RELATIONAL];
};
