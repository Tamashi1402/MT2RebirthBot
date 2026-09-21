// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_clear                      ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray_clear)║
// ║ Desc: Clear all elements from JSON array      ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_clear'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_clear",
      "message0": "Clear array %1",
      "args0": [
        { "type": "input_value", "name": "ARRAY", "check": "Array" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Remove all elements from a JSON array (list)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_clear'] = function(block) {
  var array = Blockly.Python.valueToCode(block, 'ARRAY', Blockly.Python.ORDER_ATOMIC) || '[]';
  return array + '.clear()\n';
};
