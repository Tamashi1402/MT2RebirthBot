// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_stringify                        ║
// ║ Category: file_manager                        ║
// ║ Source: Extra                                  ║
// ║ Desc: Convert dict/list to JSON string       ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_stringify'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_stringify",
      "message0": "To JSON string %1",
      "args0": [
        { "type": "input_value", "name": "DATA" }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Serialize a dict/list to a JSON string"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_stringify'] = function(block) {
  var data = Blockly.Python.valueToCode(block, 'DATA', Blockly.Python.ORDER_ATOMIC) || '{}';
  return ['json.dumps(' + data + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
