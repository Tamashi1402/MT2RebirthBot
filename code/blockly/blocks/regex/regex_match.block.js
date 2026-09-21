// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_regex_match                          ║
// ║ Category: regex                               ║
// ║ Library: re                                    ║
// ║ Desc: Check if string matches pattern         ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_regex_match'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_regex_match", "message0": "Does %1 match pattern %2",
      "args0": [
        { "type": "input_value", "name": "TEXT", "check": "String" },
        { "type": "input_value", "name": "PATTERN", "check": "String" }
      ],
      "inputsInline": true, "output": "Boolean", "colour": 210,
      "tooltip": "Check if a string matches a regex pattern"
    });
  }
};

Blockly.Python['pcr_regex_match'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || "''";
  var pattern = Blockly.Python.valueToCode(block, 'PATTERN', Blockly.Python.ORDER_NONE) || "''";
  return ['bool(re.search(' + pattern + ', ' + text + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
