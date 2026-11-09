// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_key_type                              ║
// ║ Category: input                               ║
// ║ Library: keyboard                              ║
// ║ Desc: Type a string of text                   ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_key_type'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_key_type",
      "message0": "Type text %1",
      "args0": [
        { "type": "input_value", "name": "TEXT", "check": "String" }
      ],
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Simulate typing a string of text"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_key_type'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'keyboard.write(' + text + ')\n';
};
