// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_point_xy — point x y                  ║
// ║ Category: resolution                          ║
// ║ Desc: A screen coordinate (x, y) you can scale  ║
// ║       or reuse across blocks                    ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_point_xy'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_point_xy",
      "message0": "point x %1 y %2",
      "args0": [
        { "type": "input_value", "name": "X", "check": "Number" },
        { "type": "input_value", "name": "Y", "check": "Number" }
      ],
      "inputsInline": true,
      "output": "Box",
      "colour": 230,
      "tooltip": "A screen coordinate (x, y). Click the crosshair button to pick it from the screen (F2), or feed it into 'scale to resolution' to make it work on any screen."
    });
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon("point", this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_point_xy'] = function(block) {
  var x = Blockly.Python.valueToCode(block, 'X', Blockly.Python.ORDER_NONE) || '0';
  var y = Blockly.Python.valueToCode(block, 'Y', Blockly.Python.ORDER_NONE) || '0';
  var code = 'point(' + x + ', ' + y + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
