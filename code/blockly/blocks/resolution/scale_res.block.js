// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_scale_res — scale to resolution       ║
// ║ Category: resolution                          ║
// ║ Desc: Scale a point/box recorded at the default ║
// ║       resolution to the current screen          ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_scale_res'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_scale_res",
      "message0": "scale %1 to screen resolution recorded at %2",
      "args0": [
        { "type": "input_value", "name": "INPUT", "check": "Box" },
        { "type": "input_value", "name": "DEFAULT", "check": "Box" }
      ],
      "inputsInline": true,
      "output": "Box",
      "colour": 230,
      "tooltip": "Takes a point (x, y) or box (x1, y1, x2, y2) you recorded at your default resolution and scales it to the current screen. Works on any resolution; on a different aspect ratio the content area is letterboxed/pillarboxed like a fullscreen game."
    });
    // arrow icon: fill the ratio in the DEFAULT socket (or add one)
    if (Blockly.icons && Blockly.icons.MFGetIcon) {
      this.addIcon(new Blockly.icons.MFGetIcon("default", this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_scale_res'] = function(block) {
  var inp = Blockly.Python.valueToCode(block, 'INPUT', Blockly.Python.ORDER_NONE) || '(0, 0)';
  var dflt = Blockly.Python.valueToCode(block, 'DEFAULT', Blockly.Python.ORDER_NONE) || 'res_spec(16, 9, 1920, 1080)';
  var code = 'res_scale(' + inp + ', ' + dflt + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
