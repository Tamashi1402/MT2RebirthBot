// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_cast_str                             ║
// ║ Category: base/type                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Cast value to string                   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_cast_str'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_cast_str",
      "message0": "str %1",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Convert a value to a string"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_cast_str'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || "''";
  return ['str(' + value + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
