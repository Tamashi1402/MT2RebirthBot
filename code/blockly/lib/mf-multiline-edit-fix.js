// MacroForge patch — make multiline text fields (the "# comment" block and
// the separator's label) stay 1:1 WHILE you type.
//
// Stock behavior has two quirks that make typed text scroll out of view
// while the editor is open:
//   1. The textarea is sized to fit the field EXACTLY (zero slack). One
//      sub-pixel of rounding and the browser scrolls inside it to keep
//      the caret visible - the top of the text slides up and out.
//   2. The field/block re-render that is supposed to re-fit the textarea
//      to freshly typed lines runs on the next animation frame
//      (queueRender), so the box lags behind the text.
// Patch:
//   - every keystroke renders the block immediately (no frame of lag), then
//     re-fits the editor box;
//   - the editor box gets a few px of slack so no internal scroll can ever
//     start - the text you see is always exactly what you typed.
(function () {
  if (typeof Blockly === "undefined" || !Blockly.FieldMultilineInput) return;
  var proto = Blockly.FieldMultilineInput.prototype;
  var origChange = proto.onHtmlInputChange_;  // inherited (captured now)
  var origResize = proto.resizeEditor_;      // inherited (captured now)
  var origCreate = proto.widgetCreate_;      // captured now

  // Slack (CSS px, workspace-scaled) so sub-pixel rounding can never make
  // the textarea's content taller than its box.
  function slack(field) {
    try { return 6 * field.workspace_.getScale(); }
    catch (e) { return 6; }
  }

  proto.resizeEditor_ = function () {
    origResize.call(this);
    try {
      var div = Blockly.WidgetDiv.getDiv();
      var h = parseFloat(div.style.height);
      if (div && this.htmlInput_ && isFinite(h)) {
        div.style.height = (h + slack(this)) + "px";
      }
    } catch (e) { /* best effort */ }
  };

  proto.onHtmlInputChange_ = function (ev) {
    origChange.call(this, ev);
    try {
      var b = this.getSourceBlock();
      if (b && b.rendered) b.render();   // immediate render (was: next frame)
      this.resizeEditor_();              // re-fit the editor box NOW
    } catch (e) { /* best effort */ }
  };

  // "Notepad mode": multiline fields show their FULL text — no "..."
  // after 50 characters. The stock Field constructor caps every field at
  // maxDisplayLength=50 (display AND while-editing width), which turns a
  // long note into "...". Infinity removes the cap for the multiline
  // note blocks only; single-line inputs keep the stock behavior.
  var origInitView = proto.initView;
  proto.initView = function () {
    this.maxDisplayLength = Infinity;   // plain instance property — direct write
    return origInitView.call(this);
  };

  // On open: fit once more after Blockly's own setup (Gecko path defers by
  // a tick; cover every path with the same sync fit).
  proto.widgetCreate_ = function () {
    var ta = origCreate.call(this);
    try {
      var b = this.getSourceBlock();
      if (b && b.rendered) b.render();
      this.resizeEditor_();
    } catch (e) { /* best effort */ }
    return ta;
  };
})();
