// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_has                              ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (json_property_exists)║
// ║ Desc: Check if JSON has a property           ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_has'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_has",
      "message0": "%1 has property %2",
      "args0": [
        { "type": "input_value", "name": "DATA" },
        { "type": "input_value", "name": "KEY", "check": "String" }
      ],
      "inputsInline": true,
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a JSON object / dict has a specific property"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_has'] = function(block) {
  var key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_ATOMIC) || "''";
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return [key + ' in ' + data, Blockly.Python.ORDER_MEMBER];
};
