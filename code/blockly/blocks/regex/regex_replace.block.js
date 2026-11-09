// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_regex_replace                        ║
// ║ Category: regex                               ║
// ║ Library: re                                    ║
// ║ Desc: Replace regex matches in string         ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_regex_replace'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_regex_replace", "message0": "In %1 replace pattern %2 with %3",
      "args0": [
        { "type": "input_value", "name": "TEXT", "check": "String" },
        { "type": "input_value", "name": "PATTERN", "check": "String" },
        { "type": "input_value", "name": "REPL", "check": "String" }
      ],
      "inputsInline": true, "output": "String", "colour": 160,
      "tooltip": "Replace all regex matches in a string with a replacement"
    });
  }
};

Blockly.Python['pcr_regex_replace'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || "''";
  var pattern = Blockly.Python.valueToCode(block, 'PATTERN', Blockly.Python.ORDER_NONE) || "''";
  var repl = Blockly.Python.valueToCode(block, 'REPL', Blockly.Python.ORDER_NONE) || "''";
  return ['re.sub(' + pattern + ', ' + repl + ', ' + text + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
