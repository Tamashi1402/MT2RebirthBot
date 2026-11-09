// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_notification                        ║
// ║ Category: system                              ║
// ║ Library: plyer                                 ║
// ║ Desc: Show desktop notification               ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_notification'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_notification",
      "message0": "Notify title %1 message %2",
      "args0": [
        { "type": "input_value", "name": "TITLE", "check": "String" },
        { "type": "input_value", "name": "MESSAGE", "check": "String" }
      ],
      "inputsInline": true, "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Show a desktop notification"
    });
  }
};

Blockly.Python['pcr_notification'] = function(block) {
  var title = Blockly.Python.valueToCode(block, 'TITLE', Blockly.Python.ORDER_NONE) || "''";
  var msg = Blockly.Python.valueToCode(block, 'MESSAGE', Blockly.Python.ORDER_NONE) || "''";
  return '_plyer_notify.notify(title=' + title + ', message=' + msg + ')\n';
};
