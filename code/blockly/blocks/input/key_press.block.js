// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_key_press                          ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_key_press'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_key_press",
      "message0": "Press key %1",
      "args0": [{ "type": "input_value", "name": "KEY", "check": ["Hotkey", "Key", "String"] }],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Press (and release) a key or a hotkey combination"
    });
  }
};

Blockly.Python['pcr_key_press'] = function(block) {
  var key = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEY', 'space') : (Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '"space"'));
  return 'macro_engine.press_key(' + key + ')\n';
};
