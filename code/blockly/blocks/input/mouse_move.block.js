// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_mouse_move                            ║
// ║ Category: input                               ║
// ║ Desc: Move mouse to a point                    ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_mouse_move'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_mouse_move",
      "message0": "Move mouse to %1",
      "args0": [
        { "type": "input_value", "name": "POINT", "check": "Box" }
      ],
      "inputsInline": true,
      "previousStatement": null,
      "nextStatement": null,
      "colour": 40,
      "tooltip": "Move the mouse cursor to a screen point (x, y)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_mouse_move'] = function(block) {
  var pt = Blockly.Python.valueToCode(block, 'POINT', Blockly.Python.ORDER_NONE) || 'point(0, 0)';
  return 'mouse_move_pt(' + pt + ')\n';
};
