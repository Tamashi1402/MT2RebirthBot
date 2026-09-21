// ╔══════════════════════════════════════════════╗
// ║ Block: lists_getSublist                         ║
// ║ Category: base/lists                          ║
// ║ Built-in: Yes                                 ║
// ║ Desc: Get sublist (slice)                    ║
// ╚══════════════════════════════════════════════╝

// ─── Python Generator ───
Blockly.Python['lists_getSublist'] = function(block) {
  var list = Blockly.Python.valueToCode(block, 'LIST', Blockly.Python.ORDER_MEMBER) || '[]';
  var where1 = block.getFieldValue('WHERE1');
  var where2 = block.getFieldValue('WHERE2');
  var at1 = Blockly.Python.valueToCode(block, 'AT1', Blockly.Python.ORDER_NONE) || '0';
  var at2 = Blockly.Python.valueToCode(block, 'AT2', Blockly.Python.ORDER_NONE) || '0';

  var start, end;
  switch (where1) {
    case 'FROM_START': start = at1; break;
    case 'FROM_END':   start = '-' + at1; break;
    case 'FIRST':      start = '0'; break;
    default:           start = at1; break;
  }
  switch (where2) {
    case 'FROM_START': end = '(int(' + at2 + ') + 1)'; break;
    case 'FROM_END':   end = '-' + at2; break;
    case 'LAST':       end = ''; break;
    default:           end = at2; break;
  }

  return [list + '[' + start + ':' + end + ']', Blockly.Python.ORDER_MEMBER];
};
