// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_size                             ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (get_json_size)  ║
// ║ Desc: Get number of properties in JSON        ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_size'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_size",
      "message0": "Size of %1",
      "args0": [
        { "type": "input_value", "name": "DATA" }
      ],
      "output": "Number",
      "colour": 230,
      "tooltip": "Get the number of properties in a JSON object / dict"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_size'] = function(block) {
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return ['len(' + data + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
