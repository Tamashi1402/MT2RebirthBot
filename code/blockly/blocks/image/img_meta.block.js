// Blocks: pcr_img_box / pcr_img_point — the pick origin of an image
// value, read at RUN TIME. Category: image (Data), but NUMBER colour
// (230): they return screen coordinates, like the point/box blocks.
// The screen picker embeds the picked region inside the resource PNG
// (tEXt "mfmeta": {box, point, screen}); these blocks read it from
// the image value at run time, so the box/point ALWAYS follow the
// current image — re-pick it and every procedure using these blocks
// gets the new coordinates, no block edits needed.
// No pick data -> (0,0,0,0) box / (0,0) point.

Blockly.Blocks['pcr_img_box'] = {
  init: function() {
    this.appendValueInput('IMG')
      .setCheck('Image')
      .appendField('get box of');
    this.setInputsInline(true);
    this.setOutput(true, 'Box');
    this.setColour(230);
    this.setTooltip('The screen box (x1, y1, x2, y2) this image was picked from — read at RUN TIME from the pick data embedded in the image. Re-pick the image and this automatically returns the new box. (0, 0, 0, 0) when the image has no pick data (screenshots, generated or unpicked images). Plugs anywhere a box fits.');
  }
};

Blockly.Python['pcr_img_box'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMG', Blockly.Python.ORDER_NONE) || 'None';
  return ['image_box(' + img + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};

Blockly.Blocks['pcr_img_point'] = {
  init: function() {
    this.appendValueInput('IMG')
      .setCheck('Image')
      .appendField('get point of');
    this.setInputsInline(true);
    this.setOutput(true, 'Box');
    this.setColour(230);
    this.setTooltip('The screen point (x, y) this image was picked from — read at RUN TIME from the pick data embedded in the image. Re-pick the image and this automatically returns the new point. (0, 0) when the image has no pick data (screenshots, generated or unpicked images). Plugs anywhere a point fits.');
  }
};

Blockly.Python['pcr_img_point'] = function(block) {
  var img = Blockly.Python.valueToCode(block, 'IMG', Blockly.Python.ORDER_NONE) || 'None';
  return ['image_point(' + img + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
