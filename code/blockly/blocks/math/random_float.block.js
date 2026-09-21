// ╔══════════════════════════════════════════════╗
// ║ Block: math_random_float                        ║
// ║ Category: base/math                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Random float 0.0–1.0                   ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['math_random_float'] = function(block) {
  return ['random.random()', Blockly.Python.ORDER_FUNCTION_CALL];
};
