// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_set                              ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (add_json_property)║
// ║ Desc: Set property in JSON/dict              ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_set'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_set",
      "message0": "Set %1 of %2 to %3",
      "args0": [
        { "type": "input_value", "name": "KEY", "check": "String" },
        { "type": "input_value", "name": "DATA" },
        { "type": "input_value", "name": "VALUE" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 270,
      "tooltip": "Set a property in a JSON object / dict"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_set'] = function(block) {
  var key = Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || "''";
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  var value = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_NONE) || 'None';
  return data + '[' + key + '] = ' + value + '\n';
};
