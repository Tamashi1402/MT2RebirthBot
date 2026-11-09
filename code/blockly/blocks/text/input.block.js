// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_text_input                           ║
// ║ Category: base/text                           ║
// ║ Built-in: No (custom)                          ║
// ║ Desc: Get user input from console             ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_text_input'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_text_input",
      "message0": "Input %1",
      "args0": [
        { "type": "input_value", "name": "PROMPT", "check": "String" }
      ],
      "output": "String",
      "colour": 160,
      "tooltip": "Get user input from the console (blocking)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_text_input'] = function(block) {
  var prompt = Blockly.Python.valueToCode(block, 'PROMPT', Blockly.Python.ORDER_NONE) || "''";
  return ['input(' + prompt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
