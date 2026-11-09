// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_time_elapsed                          ║
// ║ Category: time                                ║
// ║ Library: time                                  ║
// ║ Desc: Elapsed time (perf_counter)             ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_time_elapsed'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_time_elapsed", "message0": "High-res timer",
      "output": "Number", "colour": 230,
      "tooltip": "Get a high-resolution performance counter (for measuring elapsed time)"
    });
  }
};

Blockly.Python['pcr_time_elapsed'] = function(block) {
  return ['time.perf_counter()', Blockly.Python.ORDER_FUNCTION_CALL];
};
