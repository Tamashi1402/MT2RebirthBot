// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_key_pressed                        ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_key_pressed'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_key_pressed",
      "message0": "Key %1 is pressed",
      "args0": [{ "type": "input_value", "name": "KEY", "check": ["Hotkey", "Key", "String"] }],
      "inputsInline": true,
      "output": "Boolean",
      "colour": 210,
      "tooltip": "True while this key (or combination) is held"
    });
  }
};

Blockly.Python['pcr_key_pressed'] = function(block) {
  var key = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEY', 'space') : (Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '"space"'));
  return ['keyboard.is_pressed(' + key + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
