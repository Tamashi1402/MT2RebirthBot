// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_date_now                              ║
// ║ Category: time                                ║
// ║ Library: datetime                              ║
// ║ Desc: Get current date (no time)               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_date_now'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_date_now", "message0": "Today's date",
      "output": null, "colour": 90,
      "tooltip": "Get the current date (without time)"
    });
  }
};

Blockly.Python['pcr_date_now'] = function(block) {
  return ['datetime.date.today()', Blockly.Python.ORDER_FUNCTION_CALL];
};
