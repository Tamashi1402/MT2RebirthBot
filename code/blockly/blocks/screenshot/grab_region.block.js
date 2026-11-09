// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_screenshot_grab                     ║
// ║ Category: screenshot                           ║
// ║ Library: pyautogui, Pillow                     ║
// ║ Desc: Grab a screen region as an Image object  ║
// ║       (in memory - no temp file round-trip)     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_screenshot_grab'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_grab",
      "message0": "grab screen region %1 as image",
      "args0": [{ "type": "input_value", "name": "BOX", "check": "Box" }],
      "inputsInline": true,
      "output": "Image",
      "colour": 300,
      "tooltip": "Capture a screen region defined by a box (x1, y1, x2, y2) into an Image you can process (scale / threshold / denoise) before OCR. Wrap the box in 'scale to resolution' to work on any screen."
    });
  }
};

Blockly.Python['pcr_screenshot_grab'] = function(block) {
  var box = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || '(0, 0, 0, 0)';
  var code = 'grab_region_box(' + box + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
