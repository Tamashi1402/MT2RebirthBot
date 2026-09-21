// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_is_empty                         ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (is_json_empty)  ║
// ║ Desc: Check if JSON/dict is empty             ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_is_empty'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_is_empty",
      "message0": "Is empty %1",
      "args0": [
        { "type": "input_value", "name": "DATA" }
      ],
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a JSON object / dict is empty"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_is_empty'] = function(block) {
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return ['len(' + data + ') == 0', Blockly.Python.ORDER_RELATIONAL];
};
