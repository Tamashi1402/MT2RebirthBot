// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_hex — color literal        ║
// ║ Category: color                             ║
// ║ Desc: A fixed color value "#RRGGBB"        ║
// ╚════════════════════════════════════════════╝

Blockly.Blocks['pcr_color_hex'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_color_hex",
      "message0": "color %1",
      "args0": [
        { "type": "field_input", "name": "HEX", "text": "#FFFFFF" }
      ],
      "output": ["Color", "String"], "colour": 20,
      "tooltip": "A fixed color, e.g. #FF0000 (red). Also accepts 3-digit hex like #F00."
    });
  }
};

Blockly.Python['pcr_color_hex'] = function(block) {
  var hex = (block.getFieldValue('HEX') || '#FFFFFF').trim();
  if (!/^[#]?[0-9A-Fa-f]{3,6}$/.test(hex)) hex = '#FFFFFF';
  if (!hex.startsWith('#')) hex = '#' + hex;
  return ['"' + hex + '"', Blockly.Python.ORDER_ATOMIC];
};
