// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_at_image — get color of  ║
// ║       an image at a pixel                  ║
// ║ Category: color                             ║
// ║ Desc: The image twin of 'get color from    ║
// ║       pixel at screen' — reads a pixel     ║
// ║       INSIDE an image (screenshot / loaded ║
// ║       image) and returns "#RRGGBB"         ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_color_at_image'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_at_image",
      "message0": "get color of %1 at pixel %2",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "POINT", "check": "Box" }
      ],
      "inputsInline": true,
      "output": "String", "colour": 20,
      "tooltip": "Read a pixel color from INSIDE an image (a screenshot, a loaded image, an image variable) at point x,y in IMAGE coordinates — top-left is 0,0. Returns '#RRGGBB', storable in a color variable."
    });
  }
};

Blockly.Python['pcr_color_at_image'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_NONE) || 'None';
  var pt = Blockly.Python.valueToCode(block, 'POINT', Blockly.Python.ORDER_NONE) || '(0, 0)';
  return ['get_pixel_color_img(' + img + ', ' + pt + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
