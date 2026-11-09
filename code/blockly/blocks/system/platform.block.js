// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_platform                             ║
// ║ Category: system                              ║
// ║ Library: platform                              ║
// ║ Desc: Get OS name / platform info              ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_platform'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_platform",
      "message0": "Platform %1",
      "args0": [
        {
          "type": "field_dropdown",
          "name": "INFO",
          "options": [
            ["system", "system"], ["version", "version"],
            ["machine", "machine"], ["processor", "processor"],
            ["node name", "node"], ["python version", "python_version"]
          ]
        }
      ],
      "output": "String", "colour": 160,
      "tooltip": "Get information about the operating system / platform"
    });
  }
};

Blockly.Python['pcr_platform'] = function(block) {
  var info = block.getFieldValue('INFO');
  if (info === 'python_version') {
    return ['platform.python_version()', Blockly.Python.ORDER_FUNCTION_CALL];
  }
  return ['platform.' + info + '()', Blockly.Python.ORDER_FUNCTION_CALL];
};
