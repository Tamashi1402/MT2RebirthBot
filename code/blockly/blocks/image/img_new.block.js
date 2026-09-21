// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_img_new                              ║
// ║ Category: image                               ║
// ║ Library: PIL (Pillow)                          ║
// ║ Desc: Create a new blank image                ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_img_new'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_img_new", "message0": "New image %1 × %2 color %3",
      "args0": [
        { "type": "input_value", "name": "WIDTH", "check": "Number" },
        { "type": "input_value", "name": "HEIGHT", "check": "Number" },
        { "type": "input_value", "name": "COLOR", "check": ["String", "Color"] }
      ],
      "inputsInline": true, "output": "Image", "colour": 300,
      "tooltip": "Create a new blank image with a solid color"
    });
  }
};

Blockly.Python['pcr_img_new'] = function(block) {
  var w = Blockly.Python.valueToCode(block, 'WIDTH', Blockly.Python.ORDER_NONE) || '100';
  var h = Blockly.Python.valueToCode(block, 'HEIGHT', Blockly.Python.ORDER_NONE) || '100';
  var color = Blockly.Python.valueToCode(block, 'COLOR', Blockly.Python.ORDER_NONE) || '(255, 255, 255)';
  // procedure namespaces get Image from the engine runtime; editor code also
  // queues the import so the generated source is self-contained
  if (Blockly.Python.definitions_) { Blockly.Python.definitions_['import_PIL_Image'] = 'from PIL import Image'; }
  return ['Image.new("RGB", (int(' + w + '), int(' + h + ')), color_rgb(' + color + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
