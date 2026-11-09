// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_is_none                              ║
// ║ Category: base/logic                          ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Check if value is None                  ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_is_none'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_is_none",
      "message0": "%1 is None",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a value is None"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_is_none'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || 'None';
  return [value + ' is None', Blockly.Python.ORDER_RELATIONAL];
};
