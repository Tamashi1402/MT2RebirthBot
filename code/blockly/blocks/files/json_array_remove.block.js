// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_remove                     ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray_remove)║
// ║ Desc: Remove element at index from array      ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_remove'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_remove",
      "message0": "Remove index %1 from array %2",
      "args0": [
        { "type": "input_value", "name": "INDEX", "check": "Number" },
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Remove an element at the given index from a JSON array"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_remove'] = function(block) {
  var index = Blockly.Python.valueToCode(block, 'INDEX', Blockly.Python.ORDER_NONE) || '0';
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return array + '.pop(int(' + index + '))\n';
};
