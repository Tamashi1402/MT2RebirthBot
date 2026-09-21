// ╔════════════════════════════════════════════╗
// ║ Block: pcr_color_rgba — color R G B A      ║
// ║ Category: color                             ║
// ║ Desc: An RGBA color with a live swatch,    ║
// ║       Blockly colour picker and a screen  ║
// ║       pipette (F2). Alpha is optional —   ║
// ║       consumers that don't support it just ║
// ║       skip it.                             ║
// ╚════════════════════════════════════════════╝

// small local helpers (the editor-page setNum lives in a closure)
function mfColorSetNum(block, inputName, val) {
  var input = block.getInput(inputName);
  if (!input || !input.connection) return;
  var child = input.connection.targetBlock();
  if (child && child.type === "math_number") { child.setFieldValue(String(val), "NUM"); return; }
  if (child) { try { child.unplug(); } catch (e) {} }
  var nb = block.workspace.newBlock("math_number");
  nb.setFieldValue(String(val), "NUM");
  try { nb.initSvg(); } catch (e) {}
  nb.outputConnection.connect(input.connection);
}

function mfColorChannel(block, inputName) {
  var input = block.getInput(inputName);
  if (!input || !input.connection) return null;
  var child = input.connection.targetBlock();
  if (child && child.type === "math_number") {
    var n = parseFloat(child.getFieldValue("NUM"));
    if (!isNaN(n)) return Math.max(0, Math.min(255, Math.round(n)));
  }
  return null; // something non-numeric is wired — leave the swatch alone
}

Blockly.Blocks['pcr_color_rgba'] = {
  init: function () {
    this.jsonInit({
      "type": "pcr_color_rgba",
      "message0": "color R %1 G %2 B %3 A %4",
      "args0": [
        { "type": "input_value", "name": "R", "check": "Number" },
        { "type": "input_value", "name": "G", "check": "Number" },
        { "type": "input_value", "name": "B", "check": "Number" },
        { "type": "input_value", "name": "A", "check": "Number" }
      ],
      "inputsInline": true,
      "output": ["Color", "String"],
      "colour": 20,
      "tooltip": "A color made of R, G, B and optional A (alpha/opacity, 0-255 each). The swatch shows the current color \u2014 click it to pick from a palette, or use the pipette to grab a color straight off the screen (F2). Alpha is optional: blocks that can't use it simply skip it (see \u201Cget opacity from color\u201D to read it back)."
    });

    // live swatch + Blockly colour picker: picking fills R/G/B
    var self = this;
    var swatch = new Blockly.FieldColour("#FFFFFF", function (hex) {
      var b = this.getSourceBlock && this.getSourceBlock();
      if (!b || b.isInFlyout) return hex;
      // Deferred by one tick — on purpose. This validator also fires
      // during workspace LOAD: Blockly applies a block's <field> values
      // (which calls this validator) BEFORE it connects the block's
      // <value> children (see domToBlockHeadless_ in Blockly core —
      // applyFieldTagNodes runs, then applyInputTagNodes). At that
      // instant R/G/B have no child yet, so calling mfColorSetNum
      // synchronously here created a BRAND NEW math_number block for
      // each — and a moment later, when the real saved R/G/B blocks
      // connected, Blockly's connection logic bumped those just-created
      // numbers out as disconnected orphans (Connection.connect_ keeps
      // the previous occupant of a socket alive when it can't find
      // anywhere else to put it). That's the "duplicated homeless
      // blocks" bug — same value, floating near the color block, R/G/B
      // affected but never A because A isn't touched here.
      // Deferring lets the real children land first: by the time this
      // runs, R/G/B already have their math_number child (from load OR
      // a previous pick), so mfColorSetNum always takes the in-place
      // "update existing" path — never creates a new block. Same result
      // for a live pick, just one tick later (imperceptible).
      setTimeout(function () {
        if (!b.workspace || b.disposed) return;
        try {
          mfColorSetNum(b, "R", parseInt(hex.slice(1, 3), 16));
          mfColorSetNum(b, "G", parseInt(hex.slice(3, 5), 16));
          mfColorSetNum(b, "B", parseInt(hex.slice(5, 7), 16));
        } catch (e) {}
      }, 0);
      return hex;
    });
    try {
      if (typeof swatch.setColours === "function") {
        swatch.setColours([
          "#000000", "#404040", "#808080", "#C0C0C0", "#FFFFFF",
          "#FF0000", "#FF8000", "#FFFF00", "#80FF00", "#00FF00",
          "#00FF80", "#00FFFF", "#0080FF", "#0000FF", "#8000FF",
          "#FF00FF", "#FF0080", "#804000", "#008040", "#408080"
        ], null);
      }
      if (typeof swatch.setColumns === "function") swatch.setColumns(5);
    } catch (e) {}
    this.appendDummyInput("SWATCH_IN")
      .appendField(swatch, "SWATCH");

    // keep the swatch in sync when R/G/B change (typed, picker or pipette)
    this.setOnChange(function (e) {
      if (!this.workspace || this.isInFlyout || this.isInFlyoutBlock) return;
      if (!e || e.type !== Blockly.Events.BLOCK_CHANGE) return;
      try {
        var r = mfColorChannel(this, "R");
        var g = mfColorChannel(this, "G");
        var b = mfColorChannel(this, "B");
        if (r === null || g === null || b === null) return;
        var hex = "#" + [r, g, b].map(function (v) { return ("0" + v.toString(16)).slice(-2); }).join("").toUpperCase();
        var f = this.getField("SWATCH");
        if (f && f.getValue() !== hex) f.setValue(hex);
      } catch (err) {}
    });

    // screen pipette (F2) — same gear-chrome icon as the other pickers
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon("color", this));
    }
  }
};

Blockly.Python['pcr_color_rgba'] = function (block) {
  var r = Blockly.Python.valueToCode(block, 'R', Blockly.Python.ORDER_NONE) || '255';
  var g = Blockly.Python.valueToCode(block, 'G', Blockly.Python.ORDER_NONE) || '255';
  var b = Blockly.Python.valueToCode(block, 'B', Blockly.Python.ORDER_NONE) || '255';
  var a = Blockly.Python.valueToCode(block, 'A', Blockly.Python.ORDER_NONE) || '255';
  return ['color(int(' + r + '), int(' + g + '), int(' + b + '), int(' + a + '))', Blockly.Python.ORDER_FUNCTION_CALL];
};
