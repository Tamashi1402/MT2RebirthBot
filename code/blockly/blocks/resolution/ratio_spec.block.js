// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_res_ratio — ratio rw:rh res WxH      ║
// ║ Category: resolution                          ║
// ║ Desc: The aspect ratio + resolution your        ║
// ║       coordinates were recorded at             ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_res_ratio'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_res_ratio",
      "message0": "ratio %1 : %2 resolution %3 x %4",
      "args0": [
        { "type": "input_value", "name": "RW", "check": "Number" },
        { "type": "input_value", "name": "RH", "check": "Number" },
        { "type": "input_value", "name": "DW", "check": "Number" },
        { "type": "input_value", "name": "DH", "check": "Number" }
      ],
      "inputsInline": true,
      "output": "Box",
      "colour": 230,
      "tooltip": "Declares the content aspect ratio and the resolution your coordinates were recorded at (default 16:9 at 1920x1080). Plug in numbers or variables. Used by 'scale to resolution'."
    });
    // arrow icon: fill this ratio with the current monitor resolution
    if (Blockly.icons && Blockly.icons.MFGetIcon) {
      this.addIcon(new Blockly.icons.MFGetIcon("ratio", this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_res_ratio'] = function(block) {
  var rw = Blockly.Python.valueToCode(block, 'RW', Blockly.Python.ORDER_NONE) || '16';
  var rh = Blockly.Python.valueToCode(block, 'RH', Blockly.Python.ORDER_NONE) || '9';
  var dw = Blockly.Python.valueToCode(block, 'DW', Blockly.Python.ORDER_NONE) || '1920';
  var dh = Blockly.Python.valueToCode(block, 'DH', Blockly.Python.ORDER_NONE) || '1080';
  var code = 'res_spec(' + rw + ', ' + rh + ', ' + dw + ', ' + dh + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
