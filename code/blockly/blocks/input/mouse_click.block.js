// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_click                        ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_click'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_click",
      "message0": "Click %1",
      "args0": [{ "type": "input_value", "name": "BUTTON", "check": ["Mouse", "Key", "String"] }],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Simulate a mouse click"
    });
  }
};

Blockly.Python['pcr_mouse_click'] = function(block) {
  var btn = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'BUTTON', 'left') : (Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_NONE) || '"left"'));
  return 'macro_engine.mouse_click(' + btn + ')\n';
};
