// ╔══════════════════════════════════════════════╗
// ║ Block: math_number                             ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Number literal                          ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_number'] = function(block) {
  var num = parseFloat(block.getFieldValue('NUM'));
  if (isNaN(num)) num = 0;
  return [String(num), Blockly.Python.ORDER_ATOMIC];
};
