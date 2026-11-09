// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_hotkey                             ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_hotkey'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_hotkey",
      "message0": "Hotkey %1",
      "args0": [
        { "type": "input_value", "name": "KEYS", "check": ["Hotkey", "Key", "String"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Press a key combination at once (plug in create hotkey with)"
    });
  }
};

Blockly.Python['pcr_hotkey'] = function(block) {
  var combo = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEYS', 'ctrl+c') : (Blockly.Python.valueToCode(block, 'KEYS', Blockly.Python.ORDER_NONE) || '"ctrl+c"'));
  return 'macro_engine.press_key(' + combo + ')\n';
};
