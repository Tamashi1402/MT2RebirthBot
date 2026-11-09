/**
 * Blockly action icons that reuse the mutator-cog chrome.
 *
 * Load AFTER Blockly 10+ (script tag or import the global).
 *
 *   <script src="blockly.min.js"></script>
 *   <script src="blockly_action_icons.js"></script>
 *
 *   this.addIcon(new Blockly.actionIcons.PickerIcon(this));
 *   this.addIcon(new Blockly.actionIcons.GetIcon(this));
 *
 *   // or JSON: extensions: ["add_picker_icon"] / ["add_get_icon"]
 *
 * Clicks:
 *   block.onPickerClick = function () { ... };
 *   block.onGetClick    = function () { ... };
 *   // or Blockly.actionIcons.onPickerClick / onGetClick
 *
 * Colours come from Blockly CSS (.blocklyIconShape / .blocklyIconSymbol).
 * Do not set fill on the glyph — a theme that restyles the cog restyles these.
 */
(function (root) {
  "use strict";
  var Blockly = root.Blockly;
  if (!Blockly || !Blockly.icons || !Blockly.icons.Icon) {
    throw new Error(
      "blockly_action_icons.js: Blockly 10+ with Blockly.icons.Icon is required."
    );
  }

  var dom = Blockly.utils.dom;
  var Svg = Blockly.utils.Svg;
  var Size = Blockly.utils.Size;
  var Icon = Blockly.icons.Icon;
  var IconType = Blockly.icons.IconType;
  var SIZE = 17;

  var PICKER_PATH = "M8 1.7 C10.15 1.7 10.7 2.95 10.7 4.05 L10.7 4.8 H11.4 V6.15 H9.3 V9.45 L11.2 12.2 V13.4 H4.8 V12.2 L6.7 9.45 V6.15 H4.6 V4.8 H5.3 V4.05 C5.3 2.95 5.85 1.7 8 1.7 Z M8 10.6 L9.55 12.95 H6.45 Z";
  var PICKER_TRANSFORM = "rotate(45 8 8)";
  var GET_PATH = "M9.7 2.5 h2.6 v8.35 H6.05 v2.2 L2.2 10.25 L6.05 5.95 v2.2 H9.7 Z";

  function drawChrome(svgRoot) {
    dom.createSvgElement(
      Svg.RECT,
      {
        class: "blocklyIconShape",
        rx: "4",
        ry: "4",
        height: "16",
        width: "16",
      },
      svgRoot
    );
  }

  function drawPickerSymbol(svgRoot) {
    var g = dom.createSvgElement(
      Svg.G,
      { transform: PICKER_TRANSFORM },
      svgRoot
    );
    // evenodd hole = opening of the pipette, shows the themed shape fill
    // (same idea as the cog axle, without a hardcoded #00f circle).
    dom.createSvgElement(
      Svg.PATH,
      {
        class: "blocklyIconSymbol",
        d: PICKER_PATH,
        "fill-rule": "evenodd",
      },
      g
    );
  }

  function drawGetSymbol(svgRoot) {
    dom.createSvgElement(
      Svg.PATH,
      { class: "blocklyIconSymbol", d: GET_PATH },
      svgRoot
    );
  }

  function ActionIcon(sourceBlock) {
    Icon.call(this, sourceBlock);
  }
  ActionIcon.prototype = Object.create(Icon.prototype);
  ActionIcon.prototype.constructor = ActionIcon;
  ActionIcon.prototype.getSize = function () {
    return new Size(SIZE, SIZE);
  };
  ActionIcon.prototype.isClickableInFlyout = function () {
    return false;
  };

  function PickerIcon(sourceBlock) {
    ActionIcon.call(this, sourceBlock);
  }
  PickerIcon.prototype = Object.create(ActionIcon.prototype);
  PickerIcon.prototype.constructor = PickerIcon;
  PickerIcon.TYPE = new IconType("action_picker");
  PickerIcon.prototype.getType = function () {
    return PickerIcon.TYPE;
  };
  PickerIcon.prototype.getWeight = function () {
    return 2;
  };
  PickerIcon.prototype.initView = function (pointerdownListener) {
    if (this.svgRoot) return;
    ActionIcon.prototype.initView.call(this, pointerdownListener);
    drawChrome(this.svgRoot);
    drawPickerSymbol(this.svgRoot);
    if (dom.addClass) {
      dom.addClass(this.svgRoot, "blocklyActionIcon");
      dom.addClass(this.svgRoot, "blocklyActionIconPicker");
    }
    if (this.setTooltip) this.setTooltip("Pick x / y");
  };
  PickerIcon.prototype.onClick = function () {
    var block = this.sourceBlock;
    if (block && typeof block.onPickerClick === "function") block.onPickerClick();
    else if (Blockly.actionIcons.onPickerClick) Blockly.actionIcons.onPickerClick(block);
  };

  function GetIcon(sourceBlock) {
    ActionIcon.call(this, sourceBlock);
  }
  GetIcon.prototype = Object.create(ActionIcon.prototype);
  GetIcon.prototype.constructor = GetIcon;
  GetIcon.TYPE = new IconType("action_get");
  GetIcon.prototype.getType = function () {
    return GetIcon.TYPE;
  };
  GetIcon.prototype.getWeight = function () {
    return 3;
  };
  GetIcon.prototype.initView = function (pointerdownListener) {
    if (this.svgRoot) return;
    ActionIcon.prototype.initView.call(this, pointerdownListener);
    drawChrome(this.svgRoot);
    drawGetSymbol(this.svgRoot);
    if (dom.addClass) {
      dom.addClass(this.svgRoot, "blocklyActionIcon");
      dom.addClass(this.svgRoot, "blocklyActionIconGet");
    }
    if (this.setTooltip) this.setTooltip("Get / read");
  };
  GetIcon.prototype.onClick = function () {
    var block = this.sourceBlock;
    if (block && typeof block.onGetClick === "function") block.onGetClick();
    else if (Blockly.actionIcons.onGetClick) Blockly.actionIcons.onGetClick(block);
  };

  function safeRegisterIcon(type, ctor) {
    var reg = Blockly.icons.registry;
    if (!reg || !reg.register) return;
    try {
      reg.register(type, ctor);
    } catch (e) {
      try {
        reg.unregister(type.toString());
      } catch (e2) {}
      try {
        reg.register(type, ctor);
      } catch (e3) {}
    }
  }

  function safeRegisterExt(name, fn) {
    if (!Blockly.Extensions) return;
    try {
      if (Blockly.Extensions.isRegistered && Blockly.Extensions.isRegistered(name)) {
        if (Blockly.Extensions.unregister) Blockly.Extensions.unregister(name);
      }
    } catch (e) {}
    try {
      Blockly.Extensions.register(name, fn);
    } catch (e) {}
  }

  safeRegisterIcon(PickerIcon.TYPE, PickerIcon);
  safeRegisterIcon(GetIcon.TYPE, GetIcon);
  safeRegisterExt("add_picker_icon", function () {
    this.addIcon(new PickerIcon(this));
  });
  safeRegisterExt("add_get_icon", function () {
    this.addIcon(new GetIcon(this));
  });

  Blockly.actionIcons = {
    PickerIcon: PickerIcon,
    GetIcon: GetIcon,
    drawChrome: drawChrome,
    drawPickerSymbol: drawPickerSymbol,
    drawGetSymbol: drawGetSymbol,
    PICKER_PATH: PICKER_PATH,
    GET_PATH: GET_PATH,
    onPickerClick: null,
    onGetClick: null,
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
