// Block: pcr_screenshot_box — save screenshot of box region to file
Blockly.Blocks['pcr_screenshot_box'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_box",
      "message0": "save screenshot of %1 to %2",
      "args0": [
        { "type": "input_value", "name": "BOX", "check": "Box" },
        { "type": "input_value", "name": "PATH", "check": ["String", "RESLOC"] }
      ],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 300,
      "tooltip": "Capture a screen region defined by a box and save it to a file"
    });
  }
};
Blockly.Python['pcr_screenshot_box'] = function(block) {
  var box = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || '(0,0,0,0)';
  var path = 'resolve_path(' + (Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''") + ')';
  var code = 'screenshot_box(' + box + ', ' + path + ')\n';
  return code;
};

// Screenshot of box to clipboard
Blockly.Blocks['pcr_screenshot_box_clipboard'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_screenshot_box_clipboard",
      "message0": "make screenshot of %1 and save to clipboard",
      "args0": [{ "type": "input_value", "name": "BOX", "check": "Box" }],
      "inputsInline": true,
      "previousStatement": null, "nextStatement": null, "colour": 300,
      "tooltip": "Capture a screen region defined by a box and copy it to the clipboard"
    });
  }
};
Blockly.Python['pcr_screenshot_box_clipboard'] = function(block) {
  var box = Blockly.Python.valueToCode(block, 'BOX', Blockly.Python.ORDER_NONE) || '(0,0,0,0)';
  return 'screenshot_box_clipboard(' + box + ')\n';
};
