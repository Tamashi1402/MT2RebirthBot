// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_at — get color from pixel ║
// ║ Category: color                             ║
// ║ Desc: Reads the screen pixel at x,y and    ║
// ║       returns "#RRGGBB" (storable in a      ║
// ║       color variable)                      ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_color_at'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_at",
      "message0": "get color from pixel at screen %1",
      "args0": [
        { "type": "input_value", "name": "POINT", "check": "Box" }
      ],
      "inputsInline": true,
      "output": "String", "colour": 20,
      "tooltip": "Read the pixel color at a screen point (x, y). Wrap the point in 'scale to resolution' to work on any screen."
    });
  }
};

Blockly.Python['pcr_color_at'] = function(block) {
  var pt = Blockly.Python.valueToCode(block, 'POINT', Blockly.Python.ORDER_NONE) || '(0, 0)';
  return ['get_pixel_color_pt(' + pt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
