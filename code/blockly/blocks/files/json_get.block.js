// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_get                              ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (get_json_text)  ║
// ║ Desc: Get property from JSON/dict             ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_get'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_get",
      "message0": "Get %1 from %2",
      "args0": [
        { "type": "input_value", "name": "KEY", "check": "String" },
        { "type": "input_value", "name": "DATA" }
      ],
      "inputsInline": true,
      "output": null,
      "colour": 270,
      "tooltip": "Get a property value from a JSON object / dict"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_get'] = function(block) {
  var key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || "''";
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return [data + '.get(' + key + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
