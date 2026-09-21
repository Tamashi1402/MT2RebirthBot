// ╔════════════════════════════════════════════╗
// ║ Blocks: pcr_color_red / green / blue       ║
// ║ Category: color                             ║
// ║ Desc: Extract one channel (0-255) from a   ║
// ║       color (#RRGGBB)                       ║
// ╚════════════════════════════════════════════╝
// NOTE: keep the literal Blockly.Blocks['pcr_color_*'] names below —
// the server toolbox scanner matches them textually.

Blockly.Blocks['pcr_color_red'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_red",
      "message0": "get red from color %1",
      "args0": [{ "type": "input_value", "name": "COLOR", "check": ["String", "Color"] }],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Get the red channel (0-255) of a color."
    });
  }
};
Blockly.Python['pcr_color_red'] = function(block) {
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || '"#000000"';
  return ['color_red(' + c + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_color_green'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_green",
      "message0": "get green from color %1",
      "args0": [{ "type": "input_value", "name": "COLOR", "check": ["String", "Color"] }],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Get the green channel (0-255) of a color."
    });
  }
};
Blockly.Python['pcr_color_green'] = function(block) {
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || '"#000000"';
  return ['color_green(' + c + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_color_blue'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_blue",
      "message0": "get blue from color %1",
      "args0": [{ "type": "input_value", "name": "COLOR", "check": ["String", "Color"] }],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Get the blue channel (0-255) of a color."
    });
  }
};
Blockly.Python['pcr_color_blue'] = function(block) {
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || '"#000000"';
  return ['color_blue(' + c + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
