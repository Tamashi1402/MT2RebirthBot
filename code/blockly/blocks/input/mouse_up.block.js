// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_up                           ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_up'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_up",
      "message0": "Release %1",
      "args0": [{ "type": "input_value", "name": "BUTTON", "check": ["Mouse", "Key", "String"] }],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Release a held mouse button"
    });
  }
};

Blockly.Python['pcr_mouse_up'] = function(block) {
  var btn = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'BUTTON', 'left') : (Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_NONE) || '"left"'));
  return 'macro_engine.mouse_up(' + btn + ')\n';
};
