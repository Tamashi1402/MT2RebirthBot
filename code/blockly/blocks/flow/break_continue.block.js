// ╔══════════════════════════════════════════════╗
// ║ Block: controls_flow_statements                 ║
// ║ Category: base/flow                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Break / Continue                        ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['controls_flow_statements'] = function(block) {
  var type = block.getFieldValue('FLOW');
  if (type === 'BREAK') {
    return 'break\n';
  } else {
    return 'continue\n';
  }
};
