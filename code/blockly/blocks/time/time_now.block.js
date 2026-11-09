// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_now                              ║
// ║ Category: time                                ║
// ║ Library: datetime                              ║
// ║ Desc: Get current datetime                     ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_now'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_now", "message0": "Current datetime",
      "output": null, "colour": 90,
      "tooltip": "Get the current date and time"
    });
  }
};

Blockly.Python['pcr_time_now'] = function(block) {
  return ['datetime.datetime.now()', Blockly.Python.ORDER_FUNCTION_CALL];
};
