// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_get                        ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray_get)  ║
// ║ Desc: Get element from array at index         ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_get'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_get",
      "message0": "Get index %1 of array %2",
      "args0": [
        { "type": "input_value", "name": "INDEX", "check": "Number" },
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "inputsInline": true,
      "output": null,
      "colour": 270,
      "tooltip": "Get an element from a JSON array at the given index"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_get'] = function(block) {
  var index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_NONE) || '0';
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return [array + '[int(' + index + ')]', Blockly.Python.ORDER_MEMBER];
};
