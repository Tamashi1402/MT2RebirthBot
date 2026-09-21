// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_clipboard_set                       ║
// ║ Category: system                              ║
// ║ Library: pyperclip                             ║
// ║ Desc: Set clipboard content                   ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_clipboard_set'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_clipboard_set", "message0": "Set clipboard to %1",
      "args0": [{ "type": "input_value", "name": "TEXT", "check": "String" }],
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Copy text to the clipboard"
    });
  }
};

Blockly.Python['pcr_clipboard_set'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'TEXT', Blockly.Python.ORDER_NONE) || "''";
  return 'pyperclip.copy(' + text + ')\n';
};
