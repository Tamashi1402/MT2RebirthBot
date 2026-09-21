// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_clipboard_get                        ║
// ║ Category: system                              ║
// ║ Library: pyperclip                             ║
// ║ Desc: Get clipboard content                   ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_clipboard_get'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_clipboard_get", "message0": "Get clipboard",
      "output": "String", "colour": 160,
      "tooltip": "Get the current text from the clipboard"
    });
  }
};

Blockly.Python['pcr_clipboard_get'] = function(block) {
  return ['pyperclip.paste()', Blockly.Python.ORDER_FUNCTION_CALL];
};
