// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_key_hold                           ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_key_hold'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_key_hold",
      "message0": "Hold key %1 for %2 seconds",
      "args0": [
        { "type": "input_value", "name": "KEY", "check": ["Hotkey", "Key", "String"] },
        { "type": "input_value", "name": "DURATION", "check": "Number" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Hold a key (or combination) down for a duration"
    });
  }
};

Blockly.Python['pcr_key_hold'] = function(block) {
  var key = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEY', 'space') : (Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '"space"'));
  var duration = Blockly.Python.valueToCode(block, 'DURATION', Blockly.Python.ORDER_NONE) || '0.5';
  return 'macro_engine.key_down(' + key + ')\ntime.sleep(' + duration + ')\nmacro_engine.key_up(' + key + ')\n';
};
