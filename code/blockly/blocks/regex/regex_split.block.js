// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_regex_split                          ║
// ║ Category: regex                               ║
// ║ Library: re                                    ║
// ║ Desc: Split string by regex pattern           ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_regex_split'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_regex_split", "message0": "Split %1 by pattern %2",
      "args0": [
        { "type": "input_value", "name": "TEXT", "check": "String" },
        { "type": "input_value", "name": "PATTERN", "check": "String" }
      ],
      "inputsInline": true, "output": "Array", "colour": 260,
      "tooltip": "Split a string using a regex pattern as delimiter"
    });
  }
};

Blockly.Python['pcr_regex_split'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_ATOMIC) || "''";
  var pattern = Blockly.Python.valueToCode(block, 'PATTERN', Blockly.Python.ORDER_NONE) || "'\\s+'";
  return ['re.split(' + pattern + ', ' + text + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
