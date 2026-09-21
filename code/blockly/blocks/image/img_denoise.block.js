// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_denoise                         ║
// ║ Category: image                                ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Remove tiny specks/noise from an Image  ║
// ║       (morphological open)                     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_denoise'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_denoise",
      "message0": "denoise %1",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" }
      ],
      "inputsInline": true,
      "output": "Image",
      "colour": 300,
      "tooltip": "Erode then dilate - strips stray 1-2px specks left by thresholding before OCR (same trick the MT2 bot uses)."
    });
  }
};

Blockly.Python['pcr_img_denoise'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_NONE) || 'None';
  var code = '(' + img + ').filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
