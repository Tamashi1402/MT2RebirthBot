Blockly.Blocks['pcr_wait_until'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_wait_until",
      "message0": "wait until %1",
      "args0": [
        { "type": "input_value", "name": "COND" }
      ],
      "message1": "max wait ms %1",
      "args1": [
        { "type": "input_value", "name": "TIMEOUT", "check": "Number", "align": "RIGHT" }
      ],
      "previousStatement": null, "nextStatement": null, "colour": 120,
      "tooltip": "Pause until the condition is true (checked every 50 ms). Empty condition waits until Stop (F9). Optional max wait in ms."
    });
  }
};

Blockly.Python['pcr_wait_until'] = function(block) {
  var cond = Blockly.Python.valueToCode(block, 'COND', Blockly.Python.ORDER_NONE) || 'False';
  var timeout = Blockly.Python.valueToCode(block, 'TIMEOUT', Blockly.Python.ORDER_NONE) || '';
  var out = '';
  if (timeout) {
    out += 'deadline = time.monotonic() + (' + timeout + ') / 1000.0\n';
  } else {
    out += 'deadline = None\n';
  }
  out += 'while not (' + cond + '):\n';
  out += '    if stopped() or (deadline is not None and time.monotonic() >= deadline):\n';
  out += '        break\n';
  out += '    time.sleep(0.05)\n';
  return out;
};
