// ╔══════════════════════════════════════════════╗
// ║ Block: pcr_hotkey_join                        ║
// ║ Category: input / Data                        ║
// ║ Desc: Key combination (mutator, like text join)║
// ╚══════════════════════════════════════════════╝
// @mf-category: Input/Data

(function () {
  function mfMutator(block, quarks) {
    if (typeof Blockly === "undefined") return null;
    if (Blockly.icons && Blockly.icons.MutatorIcon) {
      return new Blockly.icons.MutatorIcon(quarks, block);
    }
    if (Blockly.Mutator) return new Blockly.Mutator(quarks, block);
    return null;
  }

  function mfReconnect(conn, block, name) {
    if (!conn) return;
    if (Blockly.icons && Blockly.icons.MutatorIcon && Blockly.icons.MutatorIcon.reconnect) {
      Blockly.icons.MutatorIcon.reconnect(conn, block, name);
      return;
    }
    if (Blockly.Mutator && Blockly.Mutator.reconnect) {
      Blockly.Mutator.reconnect(conn, block, name);
      return;
    }
    var input = block.getInput(name);
    if (input && input.connection) {
      if (input.connection.isConnected()) input.connection.disconnect();
      input.connection.connect(conn);
    }
  }

  Blockly.Blocks.pcr_hotkey_join_container = {
    init: function () {
      this.appendDummyInput().appendField("hotkey keys");
      this.appendStatementInput("STACK");
      this.setColour(40);
      this.contextMenu = false;
    }
  };

  Blockly.Blocks.pcr_hotkey_join_item = {
    init: function () {
      this.appendDummyInput().appendField("key");
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(40);
      this.contextMenu = false;
    }
  };

  Blockly.Blocks["pcr_hotkey_join"] = {
    init: function () {
      this.itemCount_ = 2;
      this.setHelpUrl("");
      this.setColour(40);
      this.setOutput(true, ["Hotkey", "Key", "String"]);
      this.setTooltip("A key combination. Click the star to add or remove keys.");
      this.setInputsInline(true);
      this.updateShape_();
      var m = mfMutator(this, ["pcr_hotkey_join_item"]);
      if (m) this.setMutator(m);
    },
    mutationToDom: function () {
      var c = (Blockly.utils && Blockly.utils.xml && Blockly.utils.xml.createElement)
        ? Blockly.utils.xml.createElement("mutation")
        : document.createElement("mutation");
      c.setAttribute("items", String(this.itemCount_));
      return c;
    },
    domToMutation: function (xml) {
      this.itemCount_ = parseInt(xml.getAttribute("items"), 10) || 0;
      this.updateShape_();
    },
    saveExtraState: function () {
      return { itemCount: this.itemCount_ };
    },
    loadExtraState: function (state) {
      this.itemCount_ = (state && state.itemCount) != null ? state.itemCount : 0;
      this.updateShape_();
    },
    decompose: function (workspace) {
      var container = workspace.newBlock("pcr_hotkey_join_container");
      container.initSvg();
      var connection = container.getInput("STACK").connection;
      for (var i = 0; i < this.itemCount_; i++) {
        var item = workspace.newBlock("pcr_hotkey_join_item");
        item.initSvg();
        connection.connect(item.previousConnection);
        connection = item.nextConnection;
      }
      return container;
    },
    compose: function (containerBlock) {
      var itemBlock = containerBlock.getInputTargetBlock("STACK");
      var connections = [];
      while (itemBlock) {
        if (!itemBlock.isInsertionMarker()) connections.push(itemBlock.valueConnection_);
        itemBlock = itemBlock.getNextBlock ? itemBlock.getNextBlock() : (itemBlock.nextConnection && itemBlock.nextConnection.targetBlock());
      }
      for (var i = 0; i < this.itemCount_; i++) {
        var input = this.getInput("ADD" + i);
        var conn = input && input.connection && input.connection.targetConnection;
        if (conn && connections.indexOf(conn) === -1) conn.disconnect();
      }
      this.itemCount_ = connections.length;
      this.updateShape_();
      for (var j = 0; j < this.itemCount_; j++) mfReconnect(connections[j], this, "ADD" + j);
    },
    saveConnections: function (containerBlock) {
      var itemBlock = containerBlock.getInputTargetBlock("STACK");
      var i = 0;
      while (itemBlock) {
        var input = this.getInput("ADD" + i);
        itemBlock.valueConnection_ = input && input.connection && input.connection.targetConnection;
        itemBlock = itemBlock.getNextBlock ? itemBlock.getNextBlock() : (itemBlock.nextConnection && itemBlock.nextConnection.targetBlock());
        i++;
      }
    },
    updateShape_: function () {
      if (this.itemCount_) {
        if (this.getInput("EMPTY")) this.removeInput("EMPTY");
      } else if (!this.getInput("EMPTY")) {
        this.appendDummyInput("EMPTY").appendField("create hotkey with");
      }
      var a;
      for (a = 0; a < this.itemCount_; a++) {
        if (!this.getInput("ADD" + a)) {
          var input = this.appendValueInput("ADD" + a).setCheck(["Key", "Hotkey", "Mouse", "String"]);
          if (a === 0) input.appendField("create hotkey with");
        }
      }
      while (this.getInput("ADD" + a)) {
        this.removeInput("ADD" + a);
        a++;
      }
    }
  };

  Blockly.Python["pcr_hotkey_join"] = function (block) {
    if (typeof mfJoinHotkeyCode === "function") return mfJoinHotkeyCode(block);
    var parts = [];
    for (var i = 0; i < (block.itemCount_ || 0); i++) {
      var c = Blockly.Python.valueToCode(block, "ADD" + i, Blockly.Python.ORDER_NONE);
      if (c) parts.push(c);
    }
    if (!parts.length) return ['""', Blockly.Python.ORDER_ATOMIC];
    return ['("+".join([' + parts.join(", ") + "]))", Blockly.Python.ORDER_FUNCTION_CALL];
  };
})();
