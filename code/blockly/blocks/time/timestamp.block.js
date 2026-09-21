// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_seconds                          ║
// ║ Category: time                                ║
// ║ Library: time                                  ║
// ║ Desc: Get epoch timestamp                      ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_seconds'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_seconds", "message0": "Unix timestamp",
      "output": "Number", "colour": 230,
      "tooltip": "Get the current time as seconds since epoch (Jan 1 1970)"
    });
  }
};

Blockly.Python['pcr_time_seconds'] = function(block) {
  return ['time.time()', Blockly.Python.ORDER_FUNCTION_CALL];
};
