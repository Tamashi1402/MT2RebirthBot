// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_cast_bool                            ║
// ║ Category: base/type                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Cast value to boolean                   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_cast_bool'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_cast_bool",
      "message0": "bool %1",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Convert a value to a boolean"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_cast_bool'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return ['bool(' + value + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
