// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_size                       ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (get_jsonarray_size)║
// ║ Desc: Get JSON array length                  ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_size'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_size",
      "message0": "Length of array %1",
      "args0": [
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "output": "Number",
      "colour": 230,
      "tooltip": "Get the number of elements in a JSON array"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_size'] = function(block) {
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return ['len(' + array + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
