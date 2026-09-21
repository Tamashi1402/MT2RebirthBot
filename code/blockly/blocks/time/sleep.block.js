// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_sleep                                 ║
// ║ Category: time                                ║
// ║ Library: time                                  ║
// ║ Desc: Sleep/delay for N seconds               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_sleep'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_sleep", "message0": "Sleep %1 ms",
      "args0": [{ "type": "input_value", "name": "SECONDS", "check": "Number" }],
      "previousStatement": null, "nextStatement": null, "colour": 120,
      "tooltip": "Pause execution for a number of milliseconds"
    });
  }
};

Blockly.Python['pcr_sleep'] = function(block) {
  var secs = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_NONE) || '1';
  return 'time.sleep((' + secs + ') / 1000.0)\n';
};
