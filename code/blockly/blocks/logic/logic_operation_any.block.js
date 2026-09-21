// ╔══════════════════════════════════════════════╗
// ║ Block: logic_operation (override)            ║
// ║ Category: logic                              ║
// ║ Desc: and / or / xor — accepts ANY type      ║
// ╚══════════════════════════════════════════════╝
//
// Replaces the stock Blockly logic_operation, whose two inputs are
// hard-checked to Boolean — you couldn't plug a text/number/image/res
// socket into it. This version accepts any type on both sides AND
// outputs any type (Python truthiness semantics):
//
//   and → `A and B`  (returns the first falsy operand, else B)
//   or  → `A or B`   (returns the first truthy operand, else B)
//   xor → boolean: exactly one side is truthy
//     emitted as `(not not A) != (not not B)` — pure syntax, no
//     bool() builtin needed, and `not not` forces parens-safe
//     truthiness for any operand expression.
//
// Truthiness (same as Python): None, False, 0, "" and empty list are
// falsy — everything else (a found image, a non-empty text, any
// non-zero number) is truthy.
//
// The per-type comparison blocks (= / ≠) stay per-type in
// typed_compare.block.js — this block is only the combiner.

Blockly.Blocks['logic_operation'] = {
  init: function() {
    this.jsonInit({
      "type": "logic_operation",
      "message0": "%1 %2 %3",
      "args0": [
        { "type": "input_value", "name": "A" },          // no check — any type
        {
          "type": "field_dropdown",
          "name": "OP",
          "options": [["and", "AND"], ["or", "OR"], ["xor", "XOR"]]
        },
        { "type": "input_value", "name": "B" }           // no check — any type
      ],
      "inputsInline": true,
      "output": null,                                    // any type out
      "colour": 210,
      "tooltip":
        "and / or / xor — works with any type. and: both sides must " +
        "be truthy; or: at least one side; xor: exactly one side. " +
        "Truthiness like Python: empty text, 0, none and empty list " +
        "count as false, everything else as true. and/or return the " +
        "matching operand itself, so you can chain them into other " +
        "blocks (e.g. \u201ctext or 'fallback'\u201d)."
    });
  }
};

// ─── Python Generator (override) ───
Blockly.Python['logic_operation'] = function(block) {
  var O = Blockly.Python;
  // and/or keep clean chained output: nested `x or y` inside an `and`
  // only gets parens when precedence actually requires them.
  var AND_ORD = O.ORDER_LOGICAL_AND || O.ORDER_AND || O.ORDER_NONE;
  var OR_ORD  = O.ORDER_LOGICAL_OR  || O.ORDER_OR  || O.ORDER_NONE;
  // xor prefixes operands with `not not`, so force parens on anything
  // weaker than atomic (e.g. `x or y` → `not not (x or y)`).
  var op = block.getFieldValue('OP');

  if (op === 'XOR') {
    // operands sit in `not not X` — X must bind tighter than `not`
    // (LOGICAL_NOT), so weaker operands (and/or/ternary) get parens
    // while atomic values and comparisons stay clean.
    var NOT_ORD = O.ORDER_LOGICAL_NOT || O.ORDER_NONE;
    var a = O.valueToCode(block, 'A', NOT_ORD) || 'None';
    var b = O.valueToCode(block, 'B', NOT_ORD) || 'None';
    return ['(not not ' + a + ') != (not not ' + b + ')',
            O.ORDER_RELATIONAL !== undefined ? O.ORDER_RELATIONAL : 11];
  }

  var order = op === 'OR' ? OR_ORD : AND_ORD;
  var x = O.valueToCode(block, 'A', order) || 'None';
  var y = O.valueToCode(block, 'B', order) || 'None';
  var kw = op === 'OR' ? 'or' : 'and';
  return [x + ' ' + kw + ' ' + y, order];
};
