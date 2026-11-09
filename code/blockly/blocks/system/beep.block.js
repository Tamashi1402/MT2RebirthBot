// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_beep                                  ║
// ║ Category: system                              ║
// ║ Library: winsound                               ║
// ║ Desc: Play a system beep                       ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_beep'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_beep", "message0": "Beep freq %1 Hz for %2 ms",
      "args0": [
        { "type": "input_value", "name": "FREQ", "check": "Number" },
        { "type": "input_value", "name": "DURATION", "check": "Number" }
      ],
      "inputsInline": true, "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Play a beep at a given frequency for a duration (Windows)"
    });
  }
};

Blockly.Python['pcr_beep'] = function(block) {
  var freq = Blockly.Python.valueToCode(block, 'FREQ', Blockly.Python.ORDER_NONE) || '440';
  var dur = Blockly.Python.valueToCode(block, 'DURATION', Blockly.Python.ORDER_NONE) || '500';
  var code = 'try:\n';
  code += '    import winsound\n';
  code += '    winsound.Beep(int(' + freq + '), int(' + dur + '))\n';
  code += 'except ImportError:\n';
  code += '    print("\\a")  # Terminal bell fallback\n';
  return code;
};
