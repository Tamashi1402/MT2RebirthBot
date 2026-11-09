// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_image_from_res — image from a       ║
// ║         resource location, rendered live       ║
// ║ Category: components                           ║
// ║ Desc: Loads the image a resource location      ║
// ║       points at (res:// or any path) and        ║
// ║       shows a scaled thumbnail on the block.    ║
// ║       Pipette icon: F2 → pick a box → the crop  ║
// ║       is saved into the workspace resources     ║
// ║       folder and used here; a box + point block ║
// ║       with the picked region drops next to it.  ║
// ╚══════════════════════════════════════════════╝

var MF_PLACEHOLDER_IMG = "data:image/svg+xml," + encodeURIComponent(
  "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='28'>" +
  "<rect width='120' height='28' rx='4' fill='#262633'/>" +
  "<text x='60' y='17' font-family='Segoe UI' font-size='10' fill='#6b6b7d' text-anchor='middle'>no image</text>" +
  "</svg>"
);
var MF_MISSING_IMG = "data:image/svg+xml," + encodeURIComponent(
  "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='28'>" +
  "<rect width='120' height='28' rx='4' fill='#3a2626'/>" +
  "<text x='60' y='17' font-family='Segoe UI' font-size='10' fill='#a06b6b' text-anchor='middle'>not found</text>" +
  "</svg>"
);

Blockly.Blocks['pcr_image_from_res'] = {
  init: function() {
    this.setInputsInline(true);
    var preview = this.appendDummyInput('PREVIEW');
    preview.appendField('image');
    preview.appendField(new Blockly.FieldImage(MF_PLACEHOLDER_IMG, 120, 28, { alt: 'image' }), 'IMG');
    this.appendValueInput('PATH')
      .setCheck(['String', 'RESLOC'])
      .appendField('resource');
    this.setOutput(true, 'Image');
    this.setColour(300);
    this.setTooltip('The image at a resource location (res://name.png in the workspace resources, or any path). Pipette icon: pick a box from the screen (F2) — the crop is saved to this workspace\'s resources and shown here, and the picked region\'s point + box are stored with it. Arrow-corner icon: drop that point and box into the editor as blocks.');
    // pipette icon → F2 box pick, crop saved to workspace resources
    if (Blockly.icons && Blockly.icons.MFPickIcon) {
      this.addIcon(new Blockly.icons.MFPickIcon('res_image', this));
    }
    // meta-drop icon → reads the pick metadata (point + box the pipette
    // saved with the crop) and drops both blocks next to this one
    if (Blockly.icons && Blockly.icons.MFMetaDropIcon) {
      this.addIcon(new Blockly.icons.MFMetaDropIcon(this));
    }
    this.mfLastSrc = null;
    var self = this;
    this.setOnChange(function () { self.mfSchedulePreview(); });
  },

  // path text from the PATH socket: plain text blocks, mode-setting getters
  // (image / resloc / string) and the config-based resloc block all resolve
  // to a previewable path; anything else (variables, expressions) stays blank.
  mfPathText: function () {
    var input = this.getInput('PATH');
    if (!input || !input.connection) return '';
    var child = input.connection.targetBlock();
    if (!child) return '';
    if (child.type === 'text') return String(child.getFieldValue('TEXT') || '');
    // look through the resource-location block (the default child for every
    // path socket now) so the preview still resolves
    if (child.type === 'pcr_res_location') {
      var inner = child.getInput && child.getInput('PATH');
      if (inner && inner.connection) {
        var ic = inner.connection.targetBlock();
        if (ic && ic.type === 'text') return String(ic.getFieldValue('TEXT') || '');
      }
      return '';
    }
    if (child.type === 'mf_get_setting_image' || child.type === 'mf_get_setting_resloc' ||
        child.type === 'mf_get_setting_string') {
      var id = String(child.getFieldValue('ID') || '');
      var items = (window._mfMappings && window._mfMappings.settings) || [];
      for (var i = 0; i < items.length; i++) {
        if (items[i] && items[i].id === id && items[i].value) {
          return String(items[i].value);
        }
      }
      return '';
    }
    if (child.type === 'mf_get_setting_bool' || child.type === 'mf_get_setting_number') return '';
    return '';
  },

  mfSchedulePreview: function () {
    if (this.isInFlyout) return;
    var self = this;
    if (self.mfPreviewTimer) return;
    self.mfPreviewTries = (self.mfPreviewTries || 0) + 1;
    self.mfPreviewTimer = setTimeout(function () {
      self.mfPreviewTimer = null;
      if (!self.rendered && self.mfPreviewTries < 8) { self.mfSchedulePreview(); return; }
      self.mfRefreshPreview();
    }, 250);
  },

  mfRefreshPreview: function () {
    if (this.isInFlyout || !this.rendered) return;
    this.mfPreviewTries = 0;
    var self = this;
    var path = self.mfPathText();
    if (!path) { self.mfSetPreviewField(MF_PLACEHOLDER_IMG, 120, 28); return; }
    var wsId = window._mfWorkspaceId || '';
    var src = '/blockly/resource_preview?ws=' + encodeURIComponent(wsId) +
              '&path=' + encodeURIComponent(path) + '&v=' + Date.now();
    if (self.mfLastSrc === src) return;
    self.mfLastSrc = src;
    var probe = new Image();
    probe.onload = function () {
      var maxW = 120, maxH = 28;
      var scale = Math.min(maxW / probe.naturalWidth, maxH / probe.naturalHeight, 1);
      self.mfSetPreviewField(src, Math.max(8, Math.round(probe.naturalWidth * scale)),
                                    Math.max(8, Math.round(probe.naturalHeight * scale)));
    };
    probe.onerror = function () {
      self.mfSetPreviewField(MF_MISSING_IMG, 120, 28);
    };
    probe.src = src;
  },

  mfSetPreviewField: function (src, w, h) {
    try {
      var input = this.getInput('PREVIEW');
      if (!input) return;
      try { input.removeField('IMG'); } catch (e) {}
      var field = new Blockly.FieldImage(src, w, h, { alt: 'image' });
      input.insertFieldAt(1, field, 'IMG');
      this.render();
    } catch (e) {}
  }
};

// ─── Python Generator ───
Blockly.Python['pcr_image_from_res'] = function(block) {
  var path = Blockly.Python.valueToCode(block, 'PATH', Blockly.Python.ORDER_NONE) || "''";
  return ['image_from_res(' + path + ')', Blockly.Python.ORDER_FUNCTION_CALL];
};
