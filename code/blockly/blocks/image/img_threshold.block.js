// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_threshold                        ║
// ║ Category: image                                 ║
// ║ Library: PIL (Pillow)                           ║
// ║ Desc: Threshold - keep only pixels brighter    ║
// ║       than a cutoff (isolate bright HUD text)   ║
// ╚════════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_threshold'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_threshold",
      "message0": "threshold %1 keep brighter than %2",
      "args0": [
        { "type": "input_value", "name": "IMAGE", "check": "Image" },
        { "type": "input_value", "name": "LEVEL", "check": "Number" }
      ],
      "inputsInline": true,
      "output": "Image",
      "colour": 300,
      "tooltip": "Convert to grayscale and keep only pixels brighter than the cutoff (0-255). The MT2 bot uses 150 to isolate bright HUD numbers from the dark panel."
    });
  }
};

Blockly.Python['pcr_img_threshold'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMAGE', Blockly.Python.ORDER_NONE) || 'None';
  var level = Blockly.Python.valueToCode(block, 'LEVEL', Blockly.Python.ORDER_NONE) || '150';
  var code = '(' + img + ").convert('L').point(lambda p, _t=float(" + level + "): 255 if p >= _t else 0)";
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
