// Block: pcr_screenshot_full — capture full screenshot to file
Blockly.Blocks['pcr_screenshot_full'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_full",
      "message0": "make screenshot and save to %1",
      "args0": [{ "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }],
      "previousStatement": null, "nextStatement": null, "colour": 300,
      "tooltip": "Capture the entire screen and save it to a file"
    });
  }
};
Blockly.Python['pcr_screenshot_full'] = function(block) {
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'pyautogui.screenshot().save(' + path + ')\n';
};

// Block: pcr_screenshot_region — capture region screenshot to file (box-based)
Blockly.Blocks['pcr_screenshot_region'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_region",
      "message0": "make screenshot of %1 and save to %2",
      "args0": [
        { "type": "input_value", "name": "BOX", "check": "Box" },
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 300,
      "tooltip": "Capture the screen region defined by a box (x1, y1, x2, y2) and save it to a file. Wrap the box in 'scale to resolution' to work on any screen."
    });
  }
};
Blockly.Python['pcr_screenshot_region'] = function(block) {
  var box = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || '(0, 0, 0, 0)';
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  return 'screenshot_box(' + box + ', ' + path + ')\n';
};

// Block: pcr_screenshot_get — full screenshot, returns temp file path (res location)
Blockly.Blocks['pcr_screenshot_get'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_get",
      "message0": "make screenshot and get path",
      "output": ["String", "RESLOC"], "colour": 270,
      "tooltip": "Full screenshot into a temp file \u2014 returns the file path as a resource location, so it plugs into \u201Cload image\u201D, \u201Csave image\u201D, OCR blocks, anything that takes a res location."
    });
  }
};
Blockly.Python['pcr_screenshot_get'] = function(block) {
  return ['screenshot_tmp()', Blockly.Python.ORDER_FUNCTION_CALL];
};
