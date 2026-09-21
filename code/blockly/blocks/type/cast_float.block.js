// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_cast_float                           ║
// ║ Category: base/type                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Cast value to float                    ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_cast_float'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_cast_float",
      "message0": "float %1",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "Number",
      "colour": 230,
      "tooltip": "Convert a value to a float"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_cast_float'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return ['float(' + value + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
