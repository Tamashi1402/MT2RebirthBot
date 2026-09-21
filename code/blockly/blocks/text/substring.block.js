// ╔══════════════════════════════════════════════╗
// ║ Block: text_getSubstring                       ║
// ║ Category: base/text                           ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Get substring (slice)                  ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['text_getSubstring'] = function(block) {
  var text = Blockly.Python.valueToCode(block, 'STRING', Blockly.Python.ORDER_MEMBER) || "''";
  var where1 = block.getFieldValue('WHERE1');
  var where2 = block.getFieldValue('WHERE2');
  var at1 = Blockly.Python.valueToCode(block, 'AT1', Blockly.Python.ORDER_NONE) || '0';
  var at2 = Blockly.Python.valueToCode(block, 'AT2', Blockly.Python.ORDER_NONE) || '0';

  // Simple case: FROM index at1 TO index at2
  var start, end;
  switch (where1) {
    case 'FROM_START': start = at1; break;
    case 'FROM_END':   start = '-' + at1; break;
    case 'FIRST':      start = '0'; break;
    default:           start = at1; break;
  }
  switch (where2) {
    case 'FROM_START': end = '(int(' + at2 + ') + 1)'; break;  // +1 because Python slice is exclusive
    case 'FROM_END':   end = '-' + at2; break;
    case 'LAST':       end = ''; break;
    default:           end = at2; break;
  }

  return [text + '[' + start + ':' + end + ']', Blockly.Python.ORDER_MEMBER];
};
