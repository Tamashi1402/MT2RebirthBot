// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_open_url                             ║
// ║ Category: system                              ║
// ║ Library: webbrowser                            ║
// ║ Desc: Open URL in default browser             ║
// ╚══════════════════════════════════════════════╝

Blockly.Blocks['pcr_open_url'] = {
  init: function() {
    this.jsonInit({
      "type": "pcr_open_url", "message0": "Open URL %1",
      "args0": [{ "type": "input_value", "name": "URL", "check": "String" }],
      "previousStatement": null, "nextStatement": null, "colour": 210,
      "tooltip": "Open a URL in the default web browser"
    });
  }
};

Blockly.Python['pcr_open_url'] = function(block) {
  var url = Blockly.Python.valueToCode(block, 'URL', Blockly.Python.ORDER_NONE) || "''";
  return 'webbrowser.open(' + url + ')\n';
};
