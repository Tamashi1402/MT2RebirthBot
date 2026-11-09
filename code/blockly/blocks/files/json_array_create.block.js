// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_json_array_create                     ║
// ║ Category: file_manager                        ║
// ║ Source: MCreator File Manager (jsonarray)      ║
// ║ Desc: Create empty JSON array (list)         ║
// ╚══════════════════════════════════════════════╝

// ─── Definition ───
Blockly.Blocks['pcr_json_array_create'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_json_array_create",
      "message0": "Create empty JSON array",
      "output": "Array",
      "colour": 260,
      "tooltip": "Create a new empty list (for JSON arrays)"
    });
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_json_array_create'] = function(block) {
  return ['[]', Blockly.Python.ORDER_ATOMIC];
};
