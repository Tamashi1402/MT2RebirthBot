// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_thread_lock                          ║
// ║ Category: threading                           ║
// ║ Library: threading                             ║
// ║ Desc: Lock (mutex) for thread-safe code        ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_thread_lock'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_thread_lock", "message0": "Lock",
      "output": null, "colour": 150,
      "tooltip": "Create a threading lock for thread-safe operations"
    });
  }
};

Blockly.Python['pcr_thread_lock'] = function(block) {
  return ['threading.Lock()', Blockly.Python.ORDER_FUNCTION_CALL];
};
