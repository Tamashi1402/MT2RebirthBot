// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_pressed                      ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_pressed'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_pressed",
      "message0": "Mouse %1 is pressed",
      "args0": [{ "type": "input_value", "name": "BUTTON", "check": ["Mouse", "Key", "String"] }],
      "inputsInline": true,
      "output": "Boolean",
      "colour": 210,
      "tooltip": "Check if a mouse button is currently held down"
    });
  }
};

Blockly.Python['pcr_mouse_pressed'] = function(block) {
  var btn = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'BUTTON', 'left') : (Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_NONE) || '"left"'));
  return ['macro_engine.is_mouse_pressed(' + btn + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
