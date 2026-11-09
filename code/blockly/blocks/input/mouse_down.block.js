// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_down                         ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_down'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_down",
      "message0": "Hold %1 down",
      "args0": [{ "type": "input_value", "name": "BUTTON", "check": ["Mouse", "Key", "String"] }],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Hold a mouse button down (pair with Release)"
    });
  }
};

Blockly.Python['pcr_mouse_down'] = function(block) {
  var btn = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'BUTTON', 'left') : (Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_NONE) || '"left"'));
  return 'macro_engine.mouse_down(' + btn + ')\n';
};
