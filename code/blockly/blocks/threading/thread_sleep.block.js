Blockly.Blocks['pcr_thread_sleep'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_thread_sleep", "message0": "Thread sleep %1 seconds",
      "args0": [{ "type": "input_value", "name": "SECONDS", "check": "Number" }],
      "previousStatement": null, "nextStatement": null, "colour": 150,
      "tooltip": "Sleep this thread. Stop (F9) wakes it within 50 ms."
    });
  }
};

Blockly.Python['pcr_thread_sleep'] = function(block) {
  var secs = Blockly.Python.valueToCode(block, 'SECONDS', Blockly.Python.ORDER_NONE) || '1';
  return (
    'end = time.monotonic() + float(' + secs + ')\n' +
    'while time.monotonic() < end and not stopped():\n' +
    '    time.sleep(min(0.05, end - time.monotonic()))\n'
  );
};
