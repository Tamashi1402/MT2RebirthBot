// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_alpha — get opacity       ║
// ║ Category: color                             ║
// ║ Desc: Extract the alpha channel (0-255)    ║
// ║       from a color                          ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_color_alpha'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_alpha",
      "message0": "get opacity from color %1",
      "args0": [
        { "type": "input_value", "name": "COLOR", "check": ["String", "Color"] }
      ],
      "inputsInline": true,
      "output": "Number", "colour": 230,
      "tooltip": "Get the alpha / opacity channel (0-255, 255 = fully opaque) of a color. Colors without an alpha (plain #RRGGBB) report 255."
    });
  }
};

Blockly.Python['pcr_color_alpha'] = function(block) {
  var c = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || '"#FFFFFF"';
  return ['color_alpha(' + c + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
