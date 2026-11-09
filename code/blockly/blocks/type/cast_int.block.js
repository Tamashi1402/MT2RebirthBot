// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_cast_int                             ║
// ║ Category: base/type                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Cast value to int                      ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_cast_int'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_cast_int",
      "message0": "int %1",
      "args0": [
        { "type": "input_value", "name": "VALUE" }
      ],
      "output": "Number",
      "colour": 230,
      "tooltip": "Convert a value to an integer"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_cast_int'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || '0';
  return ['int(' + value + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
