// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_regex_find                           ║
// ║ Category: regex                               ║
// ║ Library: re                                    ║
// ║ Desc: Find all matches in string              ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_regex_find'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_regex_find", "message0": "Find all %1 in %2",
      "args0": [
        { "type": "input_value", "name": "PATTERN", "check": "String" },
        { "type": "input_value", "name": "TEXT", "check": "String" }
      ],
      "inputsInline": true, "output": "Array", "colour": 260,
      "tooltip": "Find all occurrences of a regex pattern in a string"
    });
  }
};

Blockly.Python['pcr_regex_find'] = function(block) {
  var pattern = Blockly.Python.valueToCode(block, 'PATTERN', Blockly.Python.ORDER_NONE) || "''";
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || "''";
  return ['re.findall(' + pattern + ', ' + text + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
