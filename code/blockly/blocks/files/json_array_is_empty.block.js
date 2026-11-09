// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_is_empty                   ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray_is_empty)║
// ║ Desc: Check if JSON array is empty            ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_is_empty'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_is_empty",
      "message0": "Array %1 is empty",
      "args0": [
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a JSON array is empty"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_is_empty'] = function(block) {
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return ['len(' + array + ') == 0', Blockly.Python.ORDER_RELATIONAL];
};
