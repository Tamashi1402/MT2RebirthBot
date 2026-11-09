// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_wait_key                           ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_wait_key'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_wait_key",
      "message0": "Wait for key %1",
      "args0": [{ "type": "input_value", "name": "KEY", "check": ["Hotkey", "Key", "String"] }],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Wait until this key (or combination) is pressed. Any key waits for the next press."
    });
  }
};

Blockly.Python['pcr_wait_key'] = function(block) {
  var key = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'KEY', 'any') : (Blockly.Python.valueToCode(block, 'KEY', Blockly.Python.ORDER_NONE) || '"any"'));
  if (key === '"any"' || key === "''" || key === '""') {
    return 'keyboard.read_event()\n';
  }
  return 'keyboard.wait(' + key + ')\n';
};
