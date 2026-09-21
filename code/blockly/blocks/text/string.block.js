// ╔══════════════════════════════════════════════╗
// ║ Block: text                                     ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: String literal                          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text'] = function(block) {
  var text = block.getFieldValue('TEXT');
  // Escape for Python string
  text = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
  return ["'" + text + "'", Blockly.Python.ORDER_ATOMIC];
};
