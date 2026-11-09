// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_drag                         ║
// ║ Category: input                               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_mouse_drag'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_drag",
      "message0": "Drag to %1 with %2",
      "args0": [
        { "type": "input_value", "name": "POINT", "check": "Box" },
        { "type": "input_value", "name": "BUTTON", "check": ["Mouse", "Key", "String"] }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Drag the mouse from its current position to a target point"
    });
  }
};

Blockly.Python['pcr_mouse_drag'] = function(block) {
  var pt = Blockly.Python.valueToCode(block, 'POINT', Blockly.Python.ORDER_NONE) || 'point(0, 0)';
  var btn = (typeof mfKeyCode === 'function' ? mfKeyCode(block, 'BUTTON', 'left') : (Blockly.Python.valueToCode(block, 'BUTTON', Blockly.Python.ORDER_NONE) || '"left"'));
  return 'mouse_drag_pt(' + pt + ', ' + btn + ')\n';
};
