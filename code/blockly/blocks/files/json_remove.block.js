// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_remove                           ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Remove property from JSON/dict          ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_remove'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_remove",
      "message0": "Remove %1 from %2",
      "args0": [
        { "type": "input_value", "name": "KEY", "check": "String" },
        { "type": "input_value", "name": "DATA" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Remove a property from a JSON object / dict"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_remove'] = function(block) {
  var key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || "''";
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return data + '.pop(' + key + ', None)\n';
};
