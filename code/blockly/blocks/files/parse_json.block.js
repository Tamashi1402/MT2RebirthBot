// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_parse_json                            ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager plugin           ║
// ║ Desc: Parse JSON string to dict              ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_parse_json'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_parse_json",
      "message0": "Parse JSON %1",
      "args0": [
        { "type": "input_value", "name": "JSON_STR", "check": "String" }
      ],
      "output": null,
      "colour": 270,
      "tooltip": "Parse a JSON string into a Python dict/list"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_parse_json'] = function(block) {
  var jsonStr = Blockly.Python.valueToCode(block, 'JSON_STR', Blockly.Python.ORDER_ATOMIC) || "''";
  var code = 'json.loads(' + jsonStr + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
