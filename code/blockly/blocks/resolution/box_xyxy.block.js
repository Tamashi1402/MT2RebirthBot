// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_box_xyxy — box x1 y1 x2 y2           ║
// ║ Category: resolution                          ║
// ║ Desc: A screen region box (x1, y1, x2, y2)     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_box_xyxy'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_box_xyxy",
      "message0": "box x1 %1 y1 %2 x2 %3 y2 %4",
      "args0": [
        { "type": "input_value", "name": "X1", "check": "Number" },
        { "type": "input_value", "name": "Y1", "check": "Number" },
        { "type": "input_value", "name": "X2", "check": "Number" },
        { "type": "input_value", "name": "Y2", "check": "Number" }
      ],
      "inputsInline": true,
      "output": "Box",
      "colour": 230,
      "tooltip": "A screen region (x1, y1, x2, y2). Click the crosshair button to pick it from the screen (F2), or feed it into 'scale to resolution', or into blocks that take a box (OCR, screenshots)."
    });
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon("box", this));
    }
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_box_xyxy'] = function(block) {
  var x1 = Blockly.Python.valueToCode(block, 'X1', Blockly.Python.ORDER_NONE) || '0';
  var y1 = Blockly.Python.valueToCode(block, 'Y1', Blockly.Python.ORDER_NONE) || '0';
  var x2 = Blockly.Python.valueToCode(block, 'X2', Blockly.Python.ORDER_NONE) || '0';
  var y2 = Blockly.Python.valueToCode(block, 'Y2', Blockly.Python.ORDER_NONE) || '0';
  var code = 'box(' + x1 + ', ' + y1 + ', ' + x2 + ', ' + y2 + ')';
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};
