// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_add                        ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray_add)  ║
// ║ Desc: Add element to JSON array               ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_add'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_add",
      "message0": "Add %1 to array %2",
      "args0": [
        { "type": "input_value", "name": "VALUE" },
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Append a value to a JSON array (list)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_add'] = function(block) {
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return array + '.append(' + value + ')\n';
};
