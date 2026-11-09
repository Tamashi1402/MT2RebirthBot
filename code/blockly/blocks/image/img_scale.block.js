// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_scale                           ║
// ║ Category: image                                ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Scale an Image by a factor (bicubic)    ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_scale'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_scale",
      "message0": "scale %1 by factor %2",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "FACTOR", "check": "Number" }
      ],
      "inputsInline": true,
      "output": "Image",
      "colour": 300,
      "tooltip": "Upscale an image by a factor with bicubic smoothing - e.g. factor 3 for small HUD text before OCR (like the MT2 bot does)."
    });
  }
};

Blockly.Python['pcr_img_scale'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_NONE) || 'None';
  var f = Blockly.Python.valueToCode(block, 'FACTOR', Blockly.Python.ORDER_NONE) || '1';
  var code = 'img_scale(' + img + ', ' + f + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
