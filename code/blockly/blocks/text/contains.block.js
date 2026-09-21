// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_text_contains                        ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Check if string contains substring      ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_text_contains'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_text_contains",
      "message0": "%1 contains %2",
      "args0": [
        { "type": "input_value", "name": "STRING", "check": "String" },
        { "type": "input_value", "name": "SUB", "check": "String" }
      ],
      "inputsInline": true,
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a string contains a substring"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_text_contains'] = function(block) {
  var str = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_NONE) || "''";
  var sub = Blockly.Python.valueToCode(block, 'SUB', Blockly.Python.ORDER_NONE) || "''";
  return [sub + ' in ' + str, Blockly.Python.ORDER_MEMBER];
};
