/* Macro Forge Blockly plugins: functions, flow signals, mappings, widgets, snippets. */
(function (global) {
  "use strict";

  function mutator(block, quarks) {
    if (Blockly.icons && Blockly.icons.MutatorIcon) return new Blockly.icons.MutatorIcon(quarks, block);
    return new Blockly.Mutator(quarks, block);
  }

  global._mfFuncRegistry = global._mfFuncRegistry || [];
  global._mfMappings = global._mfMappings || { config: [], settings: [], dashboard: [], toggles: [], procedures: [], widgets: [], flow: [] };
  global._mfWidgets = global._mfWidgets || [];
  global._mfFlowNodes = global._mfFlowNodes || [];
  global._mfCurrentProc = global._mfCurrentProc || "";
  global._pcrCallableProcs = global._pcrCallableProcs || [];

  function ident(s) {
    return String(s || "x").replace(/[^A-Za-z0-9_]/g, "_").replace(/^([0-9])/, "_$1");
  }

  function procList() {
    var procs = [];
    function add(p) {
      if (!p) return;
      var name = typeof p === "string" ? p : (p.label || p.name || p.id || "");
      if (name && procs.indexOf(name) < 0) procs.push(name);
    }
    add(global._mfCurrentProc);
    (global._pcrCallableProcs || []).forEach(add);
    (global._mfFuncRegistry || []).forEach(function (f) { add(f.proc); });
    return procs.length ? procs.map(function (p) { return [p, p]; }) : [["(this procedure)", global._mfCurrentProc || ""]];
  }

  function fnsFor(proc, onlyReturn) {
    var want = String(proc || "");
    return (global._mfFuncRegistry || []).filter(function (f) {
      if (String(f.proc || "") !== want) return false;
      if (onlyReturn) return (f.outputs || []).length > 0;
      return true;
    });
  }

  /* Function dropdown list for a picked procedure: its own functions PLUS
     the flow-declared globals (proc: ''). Flow functions are callable from
     every procedure, so hiding them behind a procedure pick made them
     unreachable. onlyReturn keeps the outputs-only filter for the
     "Call ... and return" family. */
  function fnsForWithFlow(proc, onlyReturn) {
    var out = fnsFor(proc, onlyReturn).slice();
    var seen = {};
    out.forEach(function (f) { seen[String(f.name || "")] = 1; });
    (global._mfFuncRegistry || []).forEach(function (f) {
      if (String(f.proc || "") !== "") return;
      if (seen[String(f.name || "")]) return;
      if (onlyReturn && !((f.outputs || []).length)) return;
      seen[String(f.name || "")] = 1;
      out.push(f);
    });
    return out;
  }

  function inferReturns(block) {
    var types = { mf_return_value: 1, pcr_return_value: 1, mf_return_text: 1, pcr_return_text: 1 };
    var list = block.getDescendants ? block.getDescendants(false) : [];
    for (var i = 0; i < list.length; i++) {
      if (types[list[i].type]) return "any";
    }
    return "none";
  }

  global.mfProcList = procList;
  global.mfFnsFor = fnsFor;

  /* ── parameter quarks (from PYCreator) ── */
  Blockly.Blocks.mf_param_string = {
    init: function () {
      this.appendDummyInput().appendField("parameter string").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(160); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_number = {
    init: function () {
      this.appendDummyInput().appendField("Parameter number").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(230); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_bool = {
    init: function () {
      this.appendDummyInput().appendField("parameter logic").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(210); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_color = {
    init: function () {
      this.appendDummyInput().appendField("parameter color").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(45); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_resloc = {
    init: function () {
      this.appendDummyInput().appendField("parameter resource location").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(270); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_image = {
    init: function () {
      this.appendDummyInput().appendField("parameter image").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(300); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_gui = {
    init: function () {
      this.appendDummyInput().appendField("parameter gui").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(345); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_param_gui_element = {
    init: function () {
      this.appendDummyInput().appendField("parameter gui element").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(325); this.contextMenu = false;
    }
  };
  var MF_PARAM_BLOCK_BY_TYPE = {
    string: "mf_param_string", number: "mf_param_number", bool: "mf_param_bool",
    color: "mf_param_color", resloc: "mf_param_resloc", image: "mf_param_image",
    gui: "mf_param_gui", gui_element: "mf_param_gui_element"
  };
  var MF_PARAM_TYPE_BY_BLOCK = {
    mf_param_string: "string", mf_param_number: "number", mf_param_bool: "bool",
    mf_param_color: "color", mf_param_resloc: "resloc", mf_param_image: "image",
    mf_param_gui: "gui", mf_param_gui_element: "gui_element"
  };
  function paramBlockType(t) { return MF_PARAM_BLOCK_BY_TYPE[t] || "mf_param_string"; }
  function paramType(bt) { return MF_PARAM_TYPE_BY_BLOCK[bt] || "string"; }

  /* ── output quarks (from PYCreator's cousin): same 8 types, dropped into the
     mutator's second stack — each becomes a value socket at the end of the
     function definition instead of a read-only labeled parameter row. ── */
  Blockly.Blocks.mf_output_string = {
    init: function () {
      this.appendDummyInput().appendField("output string").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(160); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_number = {
    init: function () {
      this.appendDummyInput().appendField("output number").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(230); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_bool = {
    init: function () {
      this.appendDummyInput().appendField("output logic").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(210); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_color = {
    init: function () {
      this.appendDummyInput().appendField("output color").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(45); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_resloc = {
    init: function () {
      this.appendDummyInput().appendField("output resource location").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(270); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_image = {
    init: function () {
      this.appendDummyInput().appendField("output image").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(300); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_gui = {
    init: function () {
      this.appendDummyInput().appendField("output gui").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(345); this.contextMenu = false;
    }
  };
  Blockly.Blocks.mf_output_gui_element = {
    init: function () {
      this.appendDummyInput().appendField("output gui element").appendField(new Blockly.FieldTextInput("value"), "PARAM_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(325); this.contextMenu = false;
    }
  };
  var MF_OUTPUT_BLOCK_BY_TYPE = {
    string: "mf_output_string", number: "mf_output_number", bool: "mf_output_bool",
    color: "mf_output_color", resloc: "mf_output_resloc", image: "mf_output_image",
    gui: "mf_output_gui", gui_element: "mf_output_gui_element"
  };
  var MF_OUTPUT_TYPE_BY_BLOCK = {
    mf_output_string: "string", mf_output_number: "number", mf_output_bool: "bool",
    mf_output_color: "color", mf_output_resloc: "resloc", mf_output_image: "image",
    mf_output_gui: "gui", mf_output_gui_element: "gui_element"
  };
  function outputBlockType(t) { return MF_OUTPUT_BLOCK_BY_TYPE[t] || "mf_output_string"; }
  function outputType(bt) { return MF_OUTPUT_TYPE_BY_BLOCK[bt] || "string"; }
  var MF_PARAM_QUARKS = ["mf_param_string", "mf_param_number", "mf_param_bool", "mf_param_color", "mf_param_resloc", "mf_param_image", "mf_param_gui", "mf_param_gui_element"];
  var MF_OUTPUT_QUARKS = ["mf_output_string", "mf_output_number", "mf_output_bool", "mf_output_color", "mf_output_resloc", "mf_output_image", "mf_output_gui", "mf_output_gui_element"];

  Blockly.Blocks.mf_func_def_mutator = {
    init: function () {
      this.appendDummyInput().appendField("pass into function:");
      this.appendStatementInput("STACK");
      this.appendDummyInput().appendField("output at the end (one socket each):");
      this.appendStatementInput("RETSTACK");
      this.setColour(120); this.contextMenu = false;
    }
  };

  Blockly.Blocks.mf_func_def = {
    init: function () {
      this.params_ = [];
      this.outputs_ = [];
      this.appendDummyInput("HEADER")
        .appendField("Function in")
        .appendField(new Blockly.FieldDropdown(procList), "PROC")
        .appendField("named")
        .appendField(new Blockly.FieldTextInput("my_function"), "NAME");
      this.appendStatementInput("DO");
      this.setColour(120);
      this.setTooltip("Floating function. Hoisted to module level. Callable from every procedure. Add outputs in the mutator for sockets at the end \u2014 the caller can fetch them back with \u201cCall function \u2026 and return\u201d.");
      this.setMutator(mutator(this, MF_PARAM_QUARKS.concat(MF_OUTPUT_QUARKS)));
    },
    mutationToDom: function () {
      var c = document.createElement("mutation");
      c.setAttribute("params", this.params_.length);
      (this.params_ || []).forEach(function (p) {
        var el = document.createElement("param");
        el.setAttribute("name", p.name); el.setAttribute("type", p.type);
        c.appendChild(el);
      });
      c.setAttribute("outputs", (this.outputs_ || []).length);
      (this.outputs_ || []).forEach(function (p) {
        var el = document.createElement("output");
        el.setAttribute("name", p.name); el.setAttribute("type", p.type);
        c.appendChild(el);
      });
      return c;
    },
    domToMutation: function (xml) {
      this.params_ = [];
      this.outputs_ = [];
      var kids = xml.children || xml.childNodes || [];
      for (var i = 0; i < kids.length; i++) {
        var n = kids[i];
        if (!n.tagName) continue;
        var tag = n.tagName.toLowerCase();
        if (tag === "param") {
          this.params_.push({ name: n.getAttribute("name") || "value", type: n.getAttribute("type") || "string" });
        } else if (tag === "output") {
          this.outputs_.push({ name: n.getAttribute("name") || "value", type: n.getAttribute("type") || "string" });
        }
      }
      this.updateShape_();
    },
    decompose: function (ws) {
      var container = ws.newBlock("mf_func_def_mutator");
      container.initSvg();
      var conn = container.getInput("STACK").connection;
      (this.params_ || []).forEach(function (p) {
        var item = ws.newBlock(paramBlockType(p.type));
        item.setFieldValue(p.name, "PARAM_NAME");
        item.initSvg(); item.render();
        conn.connect(item.previousConnection);
        conn = item.nextConnection;
      });
      var conn2 = container.getInput("RETSTACK").connection;
      (this.outputs_ || []).forEach(function (p) {
        var item = ws.newBlock(outputBlockType(p.type));
        item.setFieldValue(p.name, "PARAM_NAME");
        item.initSvg(); item.render();
        conn2.connect(item.previousConnection);
        conn2 = item.nextConnection;
      });
      return container;
    },
    compose: function (container) {
      var params = [];
      var item = container.getInputTargetBlock("STACK");
      while (item) {
        params.push({ name: item.getFieldValue("PARAM_NAME"), type: paramType(item.type) });
        item = item.nextConnection && item.nextConnection.targetBlock();
      }
      this.params_ = params;
      var outputs = [];
      var oitem = container.getInputTargetBlock("RETSTACK");
      while (oitem) {
        outputs.push({ name: oitem.getFieldValue("PARAM_NAME"), type: outputType(oitem.type) });
        oitem = oitem.nextConnection && oitem.nextConnection.targetBlock();
      }
      this.outputs_ = outputs;
      this.updateShape_();
    },
    saveConnections: function () {},
    updateShape_: function () {
      var body = null;
      var doIn = this.getInput("DO");
      if (doIn && doIn.connection.targetBlock()) body = doIn.connection.targetBlock();
      var oldOut = [];
      for (var k = 0; k < 24; k++) {
        var oi = this.getInput("OUT" + k);
        oldOut.push(oi && oi.connection ? oi.connection.targetBlock() : null);
      }
      for (var i = this.inputList.length - 1; i >= 0; i--) {
        if (this.inputList[i].name !== "HEADER") this.removeInput(this.inputList[i].name);
      }
      (this.params_ || []).forEach(function (p, i) {
        this.appendDummyInput("PARAM" + i).appendField("    " + p.name + ":").appendField(new Blockly.FieldLabel(p.type));
      }, this);
      this.appendStatementInput("DO");
      if (body) {
        try { this.getInput("DO").connection.connect(body.previousConnection); } catch (e) {}
      }
      (this.outputs_ || []).forEach(function (p, i) {
        var input = this.appendValueInput("OUT" + i).setAlign(Blockly.ALIGN_RIGHT).appendField(p.name + " (" + p.type + "):");
        if (oldOut[i] && input.connection) {
          try { input.connection.connect(oldOut[i].outputConnection); } catch (e) {}
        }
      }, this);
      if (this.rendered) this.render();
    }
  };

  Blockly.Python.mf_func_def = function (block) {
    var proc = ident(block.getFieldValue("PROC") || global._mfCurrentProc || "proc");
    var name = ident(block.getFieldValue("NAME") || "my_function");
    var params = block.params_ || [];
    var list = params.map(function (p) { return ident(p.name); });
    var body = Blockly.Python.statementToCode(block, "DO") || Blockly.Python.INDENT + "pass\n";
    var outs = block.outputs_ || [];
    var tail = "";
    if (outs.length) {
      var pairs = outs.map(function (p, i) {
        var expr = Blockly.Python.valueToCode(block, "OUT" + i, Blockly.Python.ORDER_NONE) || "None";
        return JSON.stringify(p.name) + ": " + expr;
      });
      tail = Blockly.Python.INDENT + "return {" + pairs.join(", ") + "}\n";
    }
    return "#@@PCR_FUNC_DEF@@\ndef func_" + proc + "_" + name + "(" + list.join(", ") + "):\n" + body + tail + "#@@PCR_FUNC_DEF_END@@\n";
  };

  function findEnclosingFuncDef(block) {
    var p = block && block.getSurroundParent ? block.getSurroundParent() : null;
    while (p) {
      if (p.type === "mf_func_def" || p.type === "pcr_func_def" || p.type === "pcr_function_hat") return p;
      p = p.getSurroundParent ? p.getSurroundParent() : null;
    }
    return null;
  }

  /* ── function value: one generic getter for every parameter type \u2014 the
     socket it plugs into decides what happens with it, so we don\u2019t need a
     getter block per type. ── */
  Blockly.Blocks.mf_func_param_get = {
    init: function () {
      this.appendDummyInput().appendField("function value")
        .appendField(new Blockly.FieldDropdown(function () {
          var b = this.getSourceBlock();
          var def = b && findEnclosingFuncDef(b);
          var params = (def && def.params_) || [];
          return params.length ? params.map(function (p) { return [p.name, p.name]; }) : [["(no parameters)", ""]];
        }), "PARAM");
      this.setOutput(true, null);
      this.setColour(120);
      this.setTooltip("Reads a value passed in by the caller of the enclosing function.");
    }
  };
  Blockly.Python.mf_func_param_get = function (b) {
    var name = b.getFieldValue("PARAM") || "";
    if (!name) return ["None", Blockly.Python.ORDER_ATOMIC];
    return [ident(name), Blockly.Python.ORDER_ATOMIC];
  };

  function lookupFn(proc, name) {
    proc = String(proc || "");
    name = String(name || "");
    var reg = global._mfFuncRegistry || [];
    var hit = reg.filter(function (f) {
      return String(f.proc || "") === proc && String(f.name || "") === name;
    })[0] || null;
    if (!hit) {
      // flow-declared functions are global (proc: '') — reachable from any
      // procedure, so the caller's picked proc must not hide them
      hit = reg.filter(function (f) {
        return String(f.proc || "") === "" && String(f.name || "") === name;
      })[0] || null;
    }
    return hit;
  }

  /* Resolve the procedure that ACTUALLY defines the block's selected
     function. The PROC field can go stale (function moved to another
     procedure, procedure renamed, or a save made while the registry
     was incomplete) — codegen used to trust it blindly and emit
     func_<wrongProc>_<fn>(...), a NameError at runtime. If the selected
     PROC doesn't define FUNC, look the function up across the whole
     registry and use its real home. */
  function resolveFnProc(block) {
    var proc = String(block.getFieldValue("PROC") || global._mfCurrentProc || "");
    var name = String(block.getFieldValue("FUNC") || "");
    var fn = lookupFn(proc, name);
    if (!fn && name) {
      var alt = (global._mfFuncRegistry || []).filter(function (f) {
        return String(f.name || "") === name;
      })[0];
      if (alt) { proc = String(alt.proc || ""); fn = alt; }
    }
    return { proc: proc, name: name, fn: fn };
  }

  function applyArgSockets(block, params) {
    block._argParams = params || [];
    var old = [];
    for (var i = 0; i < 24; i++) {
      var inp = block.getInput("ARG" + i);
      old.push(inp && inp.connection ? inp.connection.targetBlock() : null);
    }
    for (var j = block.inputList.length - 1; j >= 0; j--) {
      if (String(block.inputList[j].name).indexOf("ARG") === 0) block.removeInput(block.inputList[j].name);
    }
    (block._argParams || []).forEach(function (p, i) {
      var input = block.appendValueInput("ARG" + i).setAlign(Blockly.ALIGN_RIGHT).appendField((p.name || "arg") + ":");
      if (old[i] && input.connection) {
        try { input.connection.connect(old[i].outputConnection); } catch (e) {}
      }
    });
    if (block.rendered) block.render();
  }

  function rebuildCallArgs(block, onlyReturn) {
    var proc = block.getFieldValue("PROC") || block.procName_ || "";
    block.procName_ = proc;
    var fn = lookupFn(proc, block.getFieldValue("FUNC"));
    if (onlyReturn && fn && !((fn.outputs || []).length)) fn = null;
    applyArgSockets(block, fn ? fn.params : (block._argParams || []));
  }

  function callMutationToDom(block) {
    var c = document.createElement("mutation");
    var params = block._argParams || [];
    c.setAttribute("args", String(params.length));
    // Persist the dropdown selections INSIDE the mutation. The FUNC/OUTPUT
    // dropdowns are dynamic (built from the function registry, which is not
    // complete while the workspace is still loading), and Blockly silently
    // REJECTS field values that aren't in the current option list — so a
    // selection can be lost on reload. The mutation is applied before the
    // fields, so we stash the saved selections here and restore them in
    // mfReapplyCallSelections() once the registry is fully loaded.
    c.setAttribute("proc", block.getFieldValue("PROC") || block.procName_ || "");
    c.setAttribute("func", block.getFieldValue("FUNC") || "");
    var outFd = block.getField("OUTPUT");
    if (outFd) c.setAttribute("output", block.getFieldValue("OUTPUT") || "");
    params.forEach(function (p) {
      var el = document.createElement("arg");
      el.setAttribute("name", p.name || "arg");
      el.setAttribute("type", p.type || "string");
      c.appendChild(el);
    });
    return c;
  }

  function callDomToMutation(block, xml) {
    var params = [];
    block._savedSel = {
      proc: xml.getAttribute("proc") || "",
      func: xml.getAttribute("func") || "",
      output: xml.getAttribute("output") || ""
    };
    var kids = xml.children || xml.childNodes || [];
    for (var i = 0; i < kids.length; i++) {
      var n = kids[i];
      if (n.tagName && n.tagName.toLowerCase() === "arg") {
        params.push({ name: n.getAttribute("name") || "arg", type: n.getAttribute("type") || "string" });
      }
    }
    applyArgSockets(block, params);
  }

  function initCall(block, isReturn) {
    block.procName_ = global._mfCurrentProc || "";
    block._argParams = [];
    block.appendDummyInput("SEL")
      .appendField(isReturn ? "Call and get" : "Call function")
      .appendField(new Blockly.FieldDropdown(procList, function (newProc) {
        var b = this.getSourceBlock();
        if (!b) return newProc;
        b.procName_ = newProc;
        var fns = fnsFor(newProc, isReturn);
        var fnField = b.getField("FUNC");
        var next = fns.length ? fns[0].name : "";
        if (fnField) {
          try { fnField.setValue(next); } catch (e) {}
        }
        rebuildCallArgs(b, isReturn);
        return newProc;
      }), "PROC");
    block.appendDummyInput("FN")
      .appendField("function")
      .appendField(new Blockly.FieldDropdown(function () {
        var b = this.getSourceBlock();
        if (!b) return [["(no functions)", ""]];
        var fns = fnsForWithFlow(b.procName_ || b.getFieldValue("PROC"), isReturn);
        return fns.length ? fns.map(function (f) { return [f.name, f.name]; }) : [["(no functions)", ""]];
      }, function (newFn) {
        var b = this.getSourceBlock();
        if (b) rebuildCallArgs(b, isReturn);
        return newFn;
      }), "FUNC");
    if (isReturn) block.setOutput(true, null);
    else { block.setPreviousStatement(true); block.setNextStatement(true); }
    block.setColour(120);
    block.setTooltip(isReturn
      ? "Call a function from this or any flow procedure and use its return value."
      : "Call a function registered on this or any flow procedure. Args match the definition.");
    block.mutationToDom = function () { return callMutationToDom(this); };
    block.domToMutation = function (xml) { callDomToMutation(this, xml); };
    block.onchange = function (e) {
      if (!this.workspace || this.isInFlyout) return;
      if (e && e.type && e.type !== Blockly.Events.BLOCK_CHANGE) return;
      if (e && e.name && e.name !== "FUNC" && e.name !== "PROC") return;
      rebuildCallArgs(this, isReturn);
    };
  }

  Blockly.Blocks.mf_func_call = { init: function () { initCall(this, false); } };
  Blockly.Blocks.mf_func_call_return = { init: function () { initCall(this, true); } };

  function genCall(block, asValue) {
    var resolved = resolveFnProc(block);
    var proc = ident(resolved.proc);
    var name = ident(resolved.name);
    var params = (resolved.fn && resolved.fn.params) || block._argParams || [];
    if (!name) return asValue ? ["None", Blockly.Python.ORDER_ATOMIC] : "pass\n";
    var args = params.map(function (p, i) {
      return Blockly.Python.valueToCode(block, "ARG" + i, Blockly.Python.ORDER_NONE) || "None";
    });
    var fnId = proc ? ("func_" + proc + "_" + name) : ("func_" + name);
    var call = fnId + "(" + args.join(", ") + ")";
    return asValue ? [call, Blockly.Python.ORDER_FUNCTION_CALL] : call + "\n";
  }
  Blockly.Python.mf_func_call = function (b) { return genCall(b, false); };
  Blockly.Python.mf_func_call_return = function (b) { return genCall(b, true); };

  /* ── Call function [proc] function [fn] and return [output]: runs the whole
     function, then reads one named output socket from its definition. ── */
  function syncCallOutputField(b) {
    var fn = lookupFn(b.procName_ || b.getFieldValue("PROC"), b.getFieldValue("FUNC"));
    var outs = (fn && fn.outputs) || [];
    var outField = b.getField("OUTPUT");
    if (outField) {
      try { outField.setValue(outs.length ? outs[0].name : ""); } catch (e) {}
    }
  }
  Blockly.Blocks.mf_func_call_output = {
    init: function () {
      this.procName_ = global._mfCurrentProc || "";
      this._argParams = [];
      this.appendDummyInput("SEL")
        .appendField("Call function")
        .appendField(new Blockly.FieldDropdown(procList, function (newProc) {
          var b = this.getSourceBlock();
          if (!b) return newProc;
          b.procName_ = newProc;
          var fns = fnsFor(newProc, true);
          var fnField = b.getField("FUNC");
          var next = fns.length ? fns[0].name : "";
          if (fnField) { try { fnField.setValue(next); } catch (e) {} }
          rebuildCallArgs(b, true);
          syncCallOutputField(b);
          return newProc;
        }), "PROC");
      this.appendDummyInput("FN")
        .appendField("function")
        .appendField(new Blockly.FieldDropdown(function () {
          var b = this.getSourceBlock();
          if (!b) return [["(no functions)", ""]];
          var fns = fnsForWithFlow(b.procName_ || b.getFieldValue("PROC"), true);
          return fns.length ? fns.map(function (f) { return [f.name, f.name]; }) : [["(no functions)", ""]];
        }, function (newFn) {
          var b = this.getSourceBlock();
          if (b) { rebuildCallArgs(b, true); syncCallOutputField(b); }
          return newFn;
        }), "FUNC");
      this.appendDummyInput("OUT")
        .appendField("and return")
        .appendField(new Blockly.FieldDropdown(function () {
          var b = this.getSourceBlock();
          var fn = b && lookupFn(b.procName_ || b.getFieldValue("PROC"), b.getFieldValue("FUNC"));
          var outs = (fn && fn.outputs) || [];
          return outs.length ? outs.map(function (o) { return [o.name, o.name]; }) : [["(no outputs)", ""]];
        }), "OUTPUT");
      this.setOutput(true, null);
      this.setColour(120);
      this.setTooltip("Calls a function (its whole body runs) and returns one of the output sockets declared at the end of its definition.");
      this.mutationToDom = function () { return callMutationToDom(this); };
      this.domToMutation = function (xml) { callDomToMutation(this, xml); };
      this.onchange = function (e) {
        if (!this.workspace || this.isInFlyout) return;
        if (e && e.type && e.type !== Blockly.Events.BLOCK_CHANGE) return;
        if (e && e.name && e.name !== "FUNC" && e.name !== "PROC") return;
        rebuildCallArgs(this, true);
      };
    }
  };
  Blockly.Python.mf_func_call_output = function (b) {
    var resolved = resolveFnProc(b);
    var proc = ident(resolved.proc);
    var name = ident(resolved.name);
    var outName = b.getFieldValue("OUTPUT") || "";
    if (!name || !outName) return ["None", Blockly.Python.ORDER_ATOMIC];
    var params = (resolved.fn && resolved.fn.params) || b._argParams || [];
    var args = params.map(function (p, i) {
      return Blockly.Python.valueToCode(b, "ARG" + i, Blockly.Python.ORDER_NONE) || "None";
    });
    var fnId = proc ? ("func_" + proc + "_" + name) : ("func_" + name);
    var call = "(" + fnId + "(" + args.join(", ") + ") or {}).get(" + JSON.stringify(outName) + ")";
    return [call, Blockly.Python.ORDER_ATOMIC];
  };

  Blockly.Blocks.mf_return_value = {
    init: function () {
      this.appendValueInput("VALUE").appendField("return");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(120);
    }
  };
  Blockly.Python.mf_return_value = function (b) {
    return "return " + (Blockly.Python.valueToCode(b, "VALUE", Blockly.Python.ORDER_NONE) || "None") + "\n";
  };
  Blockly.Blocks.mf_return_none = {
    init: function () {
      this.appendDummyInput().appendField("return");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(120);
    }
  };
  Blockly.Python.mf_return_none = function () { return "return\n"; };

  Blockly.Blocks.mf_proc_call = {
    init: function () {
      this.appendDummyInput().appendField("call").appendField(new Blockly.FieldDropdown(function () {
        var procs = global._pcrCallableProcs || [];
        if (!procs.length) return [["(no procedures)", ""]];
        return procs.map(function (p) { return [p.id || p.label || p, p.id || p]; });
      }), "PROC_NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(120);
    }
  };
  Blockly.Python.mf_proc_call = function (b) {
    var name = b.getFieldValue("PROC_NAME");
    if (!name) return "pass\n";
    return "proc_" + ident(name) + "()\n";
  };
  Blockly.Blocks.mf_proc_call_return = {
    init: function () {
      this.appendDummyInput().appendField("call and get").appendField(new Blockly.FieldDropdown(function () {
        var procs = global._pcrCallableProcs || [];
        if (!procs.length) return [["(no procedures)", ""]];
        return procs.map(function (p) { return [p.id || p.label || p, p.id || p]; });
      }), "PROC_NAME");
      this.setOutput(true, null); this.setColour(120);
    }
  };
  Blockly.Python.mf_proc_call_return = function (b) {
    var name = b.getFieldValue("PROC_NAME");
    if (!name) return ["None", Blockly.Python.ORDER_ATOMIC];
    return ["proc_" + ident(name) + "()", Blockly.Python.ORDER_FUNCTION_CALL];
  };

  /* ── flow signal / wait / jump ── */
  Blockly.Blocks.mf_return_signal = {
    init: function () {
      this.appendDummyInput().appendField("Return flow signal")
        .appendField(new Blockly.FieldDropdown(function () {
          var nodes = global._mfFlowNodes || [];
          var ch = ["next"];
          nodes.forEach(function (n) { (n.channels || []).forEach(function (c) { if (ch.indexOf(c) < 0) ch.push(c); }); });
          return ch.map(function (c) { return [c, c]; });
        }), "SIG");
      this.setPreviousStatement(true); this.setColour(210);
      this.setTooltip("Ends this procedure and routes via that channel. Plain return = next.");
    }
  };
  Blockly.Python.mf_return_signal = function (b) {
    return "macroforge.engine.flow.signal(" + JSON.stringify(b.getFieldValue("SIG") || "next") + ")\nreturn " + JSON.stringify(b.getFieldValue("SIG") || "next") + "\n";
  };
  Blockly.Blocks.mf_skip_block = {
    init: function () {
      this.appendDummyInput().appendField("Skip current flow block");
      this.setPreviousStatement(true); this.setColour(210);
    }
  };
  Blockly.Python.mf_skip_block = function () { return "macroforge.engine.flow.skip()\nreturn 'next'\n"; };

  /* ── flow control (state hats) — dropdown-driven, no free IDs ── */
  function _mfStateOptions() {
    var nodes = global._mfFlowNodes || [];
    return nodes.length ? nodes.map(function (n) {
      return [n.label || n.id, n.id];
    }) : [["(no states)", ""]];
  }
  function _mfStateForBlock(name) {
    var dec = global._mfDeclared || [];
    for (var i = 0; i < dec.length; i++) {
      if (dec[i] && dec[i].name === name) return dec[i].state || '';
    }
    return '';
  }
  Blockly.Blocks.mf_stop_flow = {
    init: function () {
      this.appendDummyInput().appendField("Stop current flow signal");
      this.setPreviousStatement(true); this.setColour(210);
      this.setTooltip("Fully stops the flow of THIS state — the walker running this procedure ends. Other states and the bot keep running.");
    }
  };
  Blockly.Python.mf_stop_flow = function () {
    return "macroforge.engine.flow.stop_walk()\nreturn 'stop'\n";
  };
  Blockly.Blocks.mf_goto_state = {
    init: function () {
      this.appendDummyInput()
        .appendField("Go to flow state")
        .appendField(new Blockly.FieldDropdown(_mfStateOptions), "STATE");
      this.setPreviousStatement(true); this.setColour(210);
      this.setTooltip("Ends this procedure and jumps to that state — its stack runs from its start (then follows its own loop setting).");
    }
  };
  Blockly.Python.mf_goto_state = function (b) {
    return "macroforge.engine.flow.jump(" + JSON.stringify(b.getFieldValue("STATE") || "") + ")\nreturn 'jump'\n";
  };
  Blockly.Blocks.mf_goto_block_of_state = {
    init: function () {
      var self = this;
      var blockDD = new Blockly.FieldDropdown(function () {
        var dec = (global._mfDeclared || []).filter(function (d) {
          return d && (d.kind === "procedure" || d.kind === "code");
        });
        return dec.length ? dec.map(function (d) {
          var k = d.kind === "code" ? "Code" : "Procedure";
          return [k + ' "' + d.name + '"', d.name];
        }) : [["(no flow blocks)", ""]];
      }, function (val) {
        if (val) {
          try { self.setFieldValue(_mfStateForBlock(val), "STATE"); } catch (e) {}
        }
        return val;
      });
      this.appendDummyInput()
        .appendField("Go to flow block")
        .appendField(blockDD, "BLOCK")
        .appendField("of state")
        .appendField(new Blockly.FieldDropdown(_mfStateOptions), "STATE");
      this.setPreviousStatement(true); this.setColour(210);
      this.setTooltip("Ends this procedure and jumps INTO that state at the chosen block — the stack continues from there.");
    }
  };
  Blockly.Python.mf_goto_block_of_state = function (b) {
    var st = b.getFieldValue("STATE") || "";
    var blk = b.getFieldValue("BLOCK") || "";
    return "macroforge.engine.flow.jump(" + JSON.stringify(st + "::" + blk) + ")\nreturn 'jump'\n";
  };

  Blockly.Blocks.mf_get_block_name = {
    init: function () {
      this.appendDummyInput().appendField("current state id");
      this.setOutput(true, "String"); this.setColour(160);
      this.setTooltip("ID of the state hat whose flow is running this procedure.");
    }
  };
  Blockly.Python.mf_get_block_name = function () {
    return ["macroforge.engine.flow.current_state()", Blockly.Python.ORDER_FUNCTION_CALL];
  };
  Blockly.Blocks.mf_get_block_id = {
    init: function () {
      this.appendDummyInput().appendField("current flow block id");
      this.setOutput(true, "String"); this.setColour(160);
    }
  };
  Blockly.Python.mf_get_block_id = function () {
    return ["macroforge.engine.flow.current_id()", Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks.mf_goto_block = {
    init: function () {
      this.appendDummyInput().appendField("Go to flow block")
        .appendField(new Blockly.FieldDropdown(function () {
          var nodes = global._mfFlowNodes || [];
          return nodes.length ? nodes.map(function (n) { return [n.id || n.label || '(none)', n.id]; }) : [["(none)", ""]];
        }), "NODE");
      this.setPreviousStatement(true); this.setColour(210);
      this.setTooltip("Pending jump — applied after this procedure returns. Bypasses lines, conditions, delays.");
    }
  };
  Blockly.Python.mf_goto_block = function (b) {
    return "macroforge.engine.flow.jump(" + JSON.stringify(b.getFieldValue("NODE") || "") + ")\n";
  };

  /* ── overlay (engine) ── */
  Blockly.Blocks.mf_overlay_set = {
    init: function () {
      this.appendValueInput("VALUE").setCheck("String")
        .appendField("Set overlay")
        .appendField(new Blockly.FieldDropdown([
          ["header", "header"],
          ["name", "name"]
        ]), "SLOT")
        .appendField("to");
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(210);
      this.setTooltip("Set an overlay text slot. Header and name live on the bot overlay.");
    }
  };
  Blockly.Python.mf_overlay_set = function (b) {
    var slot = JSON.stringify(b.getFieldValue("SLOT") || "header");
    var value = Blockly.Python.valueToCode(b, "VALUE", Blockly.Python.ORDER_NONE) || "''";
    return "macroforge.engine.functions.call(\"macroforge.engine.overlay.set\", " + slot + ", " + value + ")\n";
  };

  Blockly.Blocks.mf_overlay_timer = {
    init: function () {
      this.appendDummyInput().appendField("overlay timer");
      this.setOutput(true, "Number");
      this.setColour(230);
      this.setTooltip("Overlay run timer in seconds.");
    }
  };
  Blockly.Python.mf_overlay_timer = function () {
    return ["macroforge.engine.functions.call(\"macroforge.engine.overlay.get\", \"timer\")", Blockly.Python.ORDER_FUNCTION_CALL];
  };

  Blockly.Blocks.mf_overlay_visible = {
    init: function () {
      this.appendValueInput("VALUE").setCheck("Boolean")
        .appendField("set overlay visible to");
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(210);
      this.setTooltip("Show or hide the bot overlay.");
    }
  };
  Blockly.Python.mf_overlay_visible = function (b) {
    var v = Blockly.Python.valueToCode(b, "VALUE", Blockly.Python.ORDER_NONE) || "True";
    return "macroforge.engine.functions.call(\"macroforge.engine.overlay.visible\", " + v + ")\n";
  };

  Blockly.Blocks.mf_overlay_timer_active = {
    init: function () {
      this.appendValueInput("VALUE").setCheck("Boolean")
        .appendField("set overlay timer active to");
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(210);
      this.setTooltip("Show or hide the run timer on the overlay HUD (requires the overlay to be active).");
    }
  };
  Blockly.Python.mf_overlay_timer_active = function (b) {
    var v = Blockly.Python.valueToCode(b, "VALUE", Blockly.Python.ORDER_NONE) || "True";
    return "macroforge.engine.functions.call(\"macroforge.engine.overlay.timer_active\", " + v + ")\n";
  };

  Blockly.Blocks.mf_overlay_set_timer = {
    init: function () {
      this.appendValueInput("SECONDS").setCheck("Number")
        .appendField("set overlay timer to");
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setColour(210);
      this.setTooltip("Set the overlay run timer to N seconds — it keeps counting up from there. Use 0 to reset it (e.g. on each rebirth finished).");
    }
  };
  Blockly.Python.mf_overlay_set_timer = function (b) {
    var v = Blockly.Python.valueToCode(b, "SECONDS", Blockly.Python.ORDER_NONE) || "0";
    return "macroforge.engine.functions.call(\"macroforge.engine.overlay.set_timer\", " + v + ")\n";
  };

  Blockly.Blocks.mf_global_get = {
    init: function () {
      this.appendDummyInput().appendField("global").appendField(new Blockly.FieldTextInput("attempts"), "KEY");
      this.setOutput(true, null); this.setColour(330);
    }
  };
  Blockly.Python.mf_global_get = function (b) {
    return ["macroforge.engine.globals.get(" + JSON.stringify(b.getFieldValue("KEY")) + ")", Blockly.Python.ORDER_FUNCTION_CALL];
  };
  Blockly.Blocks.mf_global_set = {
    init: function () {
      this.appendValueInput("VAL").appendField("set global").appendField(new Blockly.FieldTextInput("attempts"), "KEY").appendField("to");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(330);
    }
  };
  Blockly.Python.mf_global_set = function (b) {
    var v = Blockly.Python.valueToCode(b, "VAL", Blockly.Python.ORDER_NONE) || "None";
    return "macroforge.engine.globals.set(" + JSON.stringify(b.getFieldValue("KEY")) + ", " + v + ")\n";
  };

  Blockly.Blocks.mf_stop_bot = {
    init: function () {
      this.appendDummyInput().appendField("stop bot");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(210);
    }
  };
  Blockly.Python.mf_stop_bot = function () { return "macroforge.engine.run.stop()\n"; };

  Blockly.Blocks.mf_steal_focus = {
    init: function () {
      this.appendDummyInput().appendField("steal focus for engine");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(210);
    }
  };
  Blockly.Python.mf_steal_focus = function () { return "macroforge.engine.window.focus_self()\n"; };

  /* ── snippets ── */
  Blockly.Blocks.mf_code_stmt = {
    init: function () {
      this.appendDummyInput().appendField("code").appendField(new Blockly.FieldMultilineInput("pass"), "CODE");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(20);
    }
  };
  Blockly.Python.mf_code_stmt = function (b) {
    var code = b.getFieldValue("CODE") || "pass";
    return code.replace(/\s+$/, "") + "\n";
  };
  Blockly.Blocks.mf_code_expr = {
    init: function () {
      this.appendDummyInput().appendField("expr").appendField(new Blockly.FieldTextInput("0"), "CODE");
      this.setOutput(true, null); this.setColour(20);
    }
  };
  Blockly.Python.mf_code_expr = function (b) {
    return [b.getFieldValue("CODE") || "None", Blockly.Python.ORDER_ATOMIC];
  };

  /* ── mapped fields + picker ── */
  function makeMappedField(value, kind, ty) {
    var field = new Blockly.FieldLabel(value || "pick\u2026");
    field.kind_ = kind;
    field.ty_ = ty;
    field.EDITABLE = true;
    field.SERIALIZABLE = true;
    field.showEditor_ = function () { openPicker(this, this.kind_, this.ty_); };
    return field;
  }

  function mappedBlock(type, label, kind, check, colour) {
    Blockly.Blocks[type] = {
      init: function () {
        this.appendDummyInput().appendField(label).appendField(makeMappedField("pick\u2026", kind, check), "ID");
        this.setOutput(true, check === "number" ? "Number" : check === "boolean" ? "Boolean" : "String");
        this.setColour(colour);
        this.setTooltip("Double-click the id to pick from " + kind + ".");
      }
    };
    Blockly.Python[type] = function (b) {
      var id = b.getFieldValue("ID") || "";
      var call =
        kind === "config" ? "macroforge.engine.config.get(" + JSON.stringify(id) + ")" :
        kind === "settings" ? "macroforge.engine.settings.get(" + JSON.stringify(id) + ")" :
        kind === "dashboard" ? "macroforge.engine.dashboard.get(" + JSON.stringify(id) + ")" :
        kind === "toggles" ? "macroforge.engine.toggles.get(" + JSON.stringify(id) + ")" :
        kind === "widgets" ? "macroforge.engine.widget.get(" + JSON.stringify(id) + ")" :
        "macroforge.engine.procedures.call(" + JSON.stringify(id) + ")";
      return [call, Blockly.Python.ORDER_FUNCTION_CALL];
    };
  }

  function mappingMenu(kind, ty) {
    return function () {
      var items = (global._mfMappings && global._mfMappings[kind]) || [];
      var want = ty === "boolean" ? "boolean" : ty === "number" ? "number" : "string";
      var opts = [];
      var seen = {};
      items.forEach(function (it) {
        if (!it || !it.id) return;
        var t = it.type || "string";
        if (t === "bool" || t === "logic") t = "boolean";
        if (t === "text") t = "string";
        if (t === "resloc" || t === "resource_location") t = "resloc";
        if (t === "key" || t === "mouse") t = "keybind";
        if (t !== want) return;
        if (seen[it.id]) return;
        seen[it.id] = true;
        opts.push([it.label || it.id, it.id]);
      });
      var cur = this.getValue && this.getValue();
      if (cur && !seen[cur]) opts.unshift([cur, cur]);
      if (!opts.length) opts.push(["(none)", ""]);
      return opts;
    };
  }

  function dropdownMappedBlock(type, label, kind, check, colour) {
    Blockly.Blocks[type] = {
      init: function () {
        this.appendDummyInput()
          .appendField(label)
          .appendField(new Blockly.FieldDropdown(mappingMenu(kind, check)), "ID");
        this.setOutput(true, check === "number" ? "Number" : check === "boolean" ? "Boolean" : "String");
        this.setColour(colour);
        this.setTooltip(label + " — colour is the type.");
      }
    };
    Blockly.Python[type] = function (b) {
      var id = b.getFieldValue("ID") || "";
      var call =
        kind === "config" ? "macroforge.engine.config.get(" + JSON.stringify(id) + ")" :
        "macroforge.engine.settings.get(" + JSON.stringify(id) + ")";
      return [call, Blockly.Python.ORDER_FUNCTION_CALL];
    };
  }

  dropdownMappedBlock("mf_get_config_number", "get config value", "config", "number", 230);
  dropdownMappedBlock("mf_get_config_string", "get config value", "config", "string", 160);
  dropdownMappedBlock("mf_get_config_bool", "get config value", "config", "boolean", 210);
  dropdownMappedBlock("mf_get_setting_number", "get mode settings value", "settings", "number", 230);
  dropdownMappedBlock("mf_get_setting_string", "get mode settings value", "settings", "string", 160);
  dropdownMappedBlock("mf_get_setting_bool", "get mode settings value", "settings", "boolean", 210);

  // ── advanced mode-settings getters: image settings secretly store the
  // res plus the box/point they were picked from; resloc settings are
  // resource locations. New types added in 2.1.61. ──
  function settingGetter(type, label, wantTypes, gen, output, colour, tip, withMetaDrop) {
    Blockly.Blocks[type] = {
      init: function () {
        this.appendDummyInput()
          .appendField(label)
          .appendField(new Blockly.FieldDropdown(function () {
            var items = (global._mfMappings && global._mfMappings.settings) || [];
            var opts = [];
            var seen = {};
            items.forEach(function (it) {
              if (!it || !it.id) return;
              var t = it.type || "string";
              if (t === "resource_location") t = "resloc";
              if (wantTypes.indexOf(t) < 0) return;
              if (seen[it.id]) return;
              seen[it.id] = true;
              opts.push([it.label || it.id, it.id]);
            });
            var cur = this.getValue && this.getValue();
            if (cur && !seen[cur]) opts.unshift([cur, cur]);
            if (!opts.length) opts.push(["(none)", ""]);
            return opts;
          }), "ID");
        this.setOutput(true, output);
        this.setColour(colour);
        this.setTooltip(tip);
        // meta-drop icon (arrow-corner): reads the pick metadata stored
        // with this setting's image — {res, box, point} in the setting
        // value, or the box/point embedded in the resource PNG (tEXt
        // "mfmeta") — and drops point + box blocks into the editor.
        if (withMetaDrop && typeof Blockly !== "undefined" && Blockly.icons && Blockly.icons.MFMetaDropIcon) {
          this.addIcon(new Blockly.icons.MFMetaDropIcon(this));
        }
        if (withMetaDrop) {
          var blk = this;
          blk.mfMetaSource = function () {
            return { setting: String(blk.getFieldValue("ID") || "") };
          };
        }
      }
    };
    Blockly.Python[type] = function (b) {
      var id = b.getFieldValue("ID") || "";
      return [gen(JSON.stringify(id)), Blockly.Python.ORDER_FUNCTION_CALL];
    };
  }

  settingGetter("mf_get_setting_key", "get key from mode settings", ["keybind", "key"],
    function (id) { return "macroforge.engine.settings.get(" + id + ")"; },
    ["Key", "Mouse", "String"], 40, "The key or mouse button stored in this mode setting.");
  settingGetter("mf_get_setting_image", "image from mode settings", ["image"],
    function (id) { return "setting_image(macroforge.engine.settings.get(" + id + "))"; },
    null, 300, "The image picked for this setting (loaded from the workspace resources). Arrow-corner icon: drop the box + point this image was picked from as blocks.", true);
  settingGetter("mf_get_setting_resloc", "resource location from mode settings", ["resloc", "image"],
    function (id) { return "setting_res(macroforge.engine.settings.get(" + id + "))"; },
    ["String", "RESLOC"], 270, "The res:// path (or file path) this setting holds — for image settings it is the picked resource itself. Arrow-corner icon: drop the box + point the image was picked from as blocks.", true);
  settingGetter("mf_get_setting_box", "box from image setting", ["image"],
    function (id) { return "setting_box(macroforge.engine.settings.get(" + id + "))"; },
    "Array", 230, "The screen box the image setting was picked from (x1, y1, x2, y2) — ready for OCR, screenshots or scale-to-resolution.");
  settingGetter("mf_get_setting_point", "point from image setting", ["image"],
    function (id) { return "setting_point(macroforge.engine.settings.get(" + id + "))"; },
    "Array", 230, "The screen point (box center) the image setting was picked from.");

  function dropdownMappedSetBlock(type, label, kind, check, colour) {
    Blockly.Blocks[type] = {
      init: function () {
        var inp = this.appendValueInput("VALUE")
          .setCheck(check === "number" ? "Number" : check === "boolean" ? "Boolean" : "String")
          .appendField(label)
          .appendField(new Blockly.FieldDropdown(mappingMenu(kind, check)), "ID")
          .appendField("to");
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        this.setInputsInline(true);
        this.setColour(colour);
        this.setTooltip(label + " — colour is the type.");
      }
    };
    Blockly.Python[type] = function (b) {
      var id = b.getFieldValue("ID") || "";
      var fallback = check === "number" ? "0" : check === "boolean" ? "False" : "''";
      var v = Blockly.Python.valueToCode(b, "VALUE", Blockly.Python.ORDER_NONE) || fallback;
      return "macroforge.engine.settings.set(" + JSON.stringify(id) + ", " + v + ")\n";
    };
  }
  dropdownMappedSetBlock("mf_set_setting_number", "set mode settings value", "settings", "number", 230);
  dropdownMappedSetBlock("mf_set_setting_string", "set mode settings value", "settings", "string", 160);
  dropdownMappedSetBlock("mf_set_setting_bool", "set mode settings value", "settings", "boolean", 210);

  mappedBlock("mf_get_dash", "get dashboard value", "dashboard", "number", 260);
  mappedBlock("mf_get_toggle", "get rail toggle", "toggles", "boolean", 210);

  /* ── widget composer ── */
  Blockly.Blocks.mf_display_widget = {
    init: function () {
      this.widget_ = { id: "w_" + Math.random().toString(36).slice(2, 8), name: "Widget", title: "Needs attention", body: "Set this in Config.", tone: "warn" };
      this.appendDummyInput().appendField("Display engine widget")
        .appendField(new Blockly.FieldLabel(this.widget_.name), "NAME");
      this.setPreviousStatement(true); this.setNextStatement(true); this.setColour(0);
      this.setTooltip("Survives Stop. Double-click to open the widget composer.");
    },
    mutationToDom: function () {
      var c = document.createElement("mutation");
      c.setAttribute("widget", JSON.stringify(this.widget_ || {}));
      return c;
    },
    domToMutation: function (xml) {
      try { this.widget_ = JSON.parse(xml.getAttribute("widget") || "{}"); } catch (e) { this.widget_ = {}; }
      var f = this.getField("NAME");
      if (f && this.widget_.name) f.setValue(this.widget_.name);
    }
  };
  Blockly.Python.mf_display_widget = function (b) {
    return "macroforge.engine.widget.show(" + JSON.stringify(b.widget_ || {}) + ")\n";
  };

  function ensureOverlay() {
    var el = document.getElementById("mf-overlay");
    if (el) return el;
    el = document.createElement("div");
    el.id = "mf-overlay";
    el.style.cssText = "display:none;position:fixed;inset:0;z-index:400;background:rgba(0,0,0,.55);align-items:center;justify-content:center;";
    document.body.appendChild(el);
    return el;
  }

  function openPicker(field, kind, ty) {
    var items = (global._mfMappings && global._mfMappings[kind]) || [];
    if (ty) items = items.filter(function (it) { return !it.type || it.type === ty || ty === "string"; });
    var el = ensureOverlay();
    el.style.display = "flex";
    var groups = {};
    items.forEach(function (it) {
      var g = it.group || kind;
      (groups[g] = groups[g] || []).push(it);
    });
    var html = '<div style="width:min(420px,92vw);max-height:70vh;overflow:auto;background:#111118;border:1px solid #2a2a35;border-radius:12px;padding:14px;color:#e0e0e8;font:13px/1.4 IBM Plex Sans,sans-serif">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><b>Pick ' + kind + '</b><button id="mf-x" style="background:none;border:0;color:#7070a0;cursor:pointer">Close</button></div>';
    html += '<input id="mf-q" placeholder="Search…" style="width:100%;height:32px;border:1px solid #2a2a35;background:#1c1c26;color:#e0e0e8;border-radius:6px;padding:0 10px;margin-bottom:10px">';
    html += '<div id="mf-list">';
    Object.keys(groups).forEach(function (g) {
      html += '<div class="g" data-g="' + g + '"><div style="font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#7070a0;margin:8px 0 4px">' + g + "</div>";
      groups[g].forEach(function (it) {
        html += '<button class="pick" data-id="' + it.id + '" data-label="' + String(it.label).replace(/"/g, "") + '" style="display:block;width:100%;text-align:left;background:#16161c;border:1px solid #2a2a35;color:#e0e0e8;border-radius:6px;padding:8px 10px;margin:4px 0;cursor:pointer">' + it.label + ' <span style="color:#7070a0;font-size:11px">' + it.id + "</span></button>";
      });
      html += "</div>";
    });
    if (!items.length) html += '<p style="color:#7070a0">Nothing mapped yet. Save the dashboard / settings first.</p>';
    html += "</div></div>";
    el.innerHTML = html;
    el.querySelector("#mf-x").onclick = function () { el.style.display = "none"; };
    el.onclick = function (e) { if (e.target === el) el.style.display = "none"; };
    el.querySelector("#mf-q").oninput = function () {
      var q = this.value.toLowerCase();
      el.querySelectorAll(".pick").forEach(function (b) {
        b.style.display = (b.dataset.label + " " + b.dataset.id).toLowerCase().indexOf(q) >= 0 ? "block" : "none";
      });
    };
    el.querySelectorAll(".pick").forEach(function (b) {
      b.onclick = function () {
        field.setValue(b.dataset.id);
        el.style.display = "none";
      };
    });
    el.querySelector("#mf-q").focus();
  }

  function openWidgetComposer(block) {
    var w = Object.assign({ id: "w_new", name: "Widget", title: "Title", body: "", tone: "warn" }, block.widget_ || {});
    function escAttr(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "\u0026amp;")
        .replace(/"/g, "\u0026quot;")
        .replace(/</g, "\u0026lt;");
    }
    function escText(s) {
      return String(s == null ? "" : s)
        .replace(/&/g, "\u0026amp;")
        .replace(/</g, "\u0026lt;");
    }
    var el = ensureOverlay();
    el.style.display = "flex";
    el.innerHTML = '<div style="width:min(440px,92vw);background:#111118;border:1px solid #2a2a35;border-radius:12px;padding:16px;color:#e0e0e8;font:13px/1.45 IBM Plex Sans,sans-serif">'
      + '<div style="display:flex;justify-content:space-between;margin-bottom:10px"><b>Engine widget</b><span style="color:#7070a0;font-size:11px">Survives Stop</span></div>'
      + '<label style="display:block;font-size:11px;color:#7070a0">Name<input id="w-name" value="' + escAttr(w.name) + '" style="display:block;width:100%;height:32px;margin:4px 0 10px;border:1px solid #2a2a35;background:#1c1c26;color:#e0e0e8;border-radius:6px;padding:0 10px"></label>'
      + '<label style="display:block;font-size:11px;color:#7070a0">Title<input id="w-title" value="' + escAttr(w.title) + '" style="display:block;width:100%;height:32px;margin:4px 0 10px;border:1px solid #2a2a35;background:#1c1c26;color:#e0e0e8;border-radius:6px;padding:0 10px"></label>'
      + '<label style="display:block;font-size:11px;color:#7070a0">Body<textarea id="w-body" rows="5" style="display:block;width:100%;margin:4px 0 10px;border:1px solid #2a2a35;background:#1c1c26;color:#e0e0e8;border-radius:6px;padding:8px 10px">' + escText(w.body) + "</textarea></label>"
      + '<label style="display:block;font-size:11px;color:#7070a0;margin-bottom:12px">Tone <select id="w-tone" style="height:32px;border:1px solid #2a2a35;background:#1c1c26;color:#e0e0e8;border-radius:6px;padding:0 8px"><option value="info">info</option><option value="warn">warn</option><option value="error">error</option></select></label>'
      + '<div style="display:flex;gap:8px"><button id="w-cancel" style="flex:1;height:36px;border:1px solid #2a2a35;background:none;color:#7070a0;border-radius:6px;cursor:pointer">Cancel</button><button id="w-save" style="flex:1;height:36px;border:0;background:#7c6af7;color:#fff;font-weight:700;border-radius:6px;cursor:pointer">Save widget</button></div>'
      + "</div>";
    el.querySelector("#w-tone").value = w.tone || "warn";
    el.querySelector("#w-cancel").onclick = function () { el.style.display = "none"; };
    el.querySelector("#w-save").onclick = function () {
      block.widget_ = {
        id: w.id,
        name: el.querySelector("#w-name").value || "Widget",
        title: el.querySelector("#w-title").value || "",
        body: el.querySelector("#w-body").value || "",
        tone: el.querySelector("#w-tone").value || "warn"
      };
      var f = block.getField("NAME");
      if (f) f.setValue(block.widget_.name);
      parent.postMessage({ type: "proc-widget-save", widget: block.widget_ }, "*");
      el.style.display = "none";
    };
  }

  global.mfOpenPicker = openPicker;
  global.mfOpenWidgetComposer = openWidgetComposer;

  global.mfScanFuncs = function (workspace) {
    var saved = (global._mfFuncRegistry || []).filter(function (f) { return f._live !== true; });
    if (!workspace) { global._mfFuncRegistry = saved; return; }
    // live definitions first, deduped against saved ones by (proc, name) —
    // a function defined in this workspace must never appear twice
    var live = [];
    var seen = {};
    workspace.getAllBlocks(false).forEach(function (b) {
      if (b.type !== "mf_func_def" && b.type !== "pcr_func_def") return;
      var proc = b.getFieldValue("PROC") || global._mfCurrentProc || "";
      var name = b.getFieldValue("NAME") || "";
      if (!name) return;
      var key = proc + "\0" + name;
      if (seen[key]) return;
      seen[key] = true;
      live.push({
        proc: proc,
        name: name,
        params: b.params_ || [],
        outputs: b.outputs_ || [],
        returns: inferReturns(b),
        _live: true
      });
    });
    global._mfFuncRegistry = live.concat(saved.filter(function (f) {
      return !seen[f.proc + "\0" + f.name];
    }));
  };

  global.mfInitCall = initCall;
  global.mfRebuildCallArgs = rebuildCallArgs;

  /* Restore PROC/FUNC/OUTPUT selections stashed in the call blocks'
     mutations. Run AFTER mfScanFuncs(workspace) — the registry must be
     complete, or the values get rejected again. FieldDropdown validates
     against its CACHED option list, so each dynamic field's cache must
     be busted (generatedOptions = null) before the value is re-set. */
  global.mfReapplyCallSelections = function (workspace) {
    if (!workspace || !workspace.getAllBlocks) return;
    workspace.getAllBlocks(false).forEach(function (b) {
      var sel = b._savedSel;
      if (!sel) return;
      delete b._savedSel;
      function setField(name, value) {
        if (!value) return;
        var f = b.getField(name);
        if (!f) return;
        try { if (f.generatedOptions !== undefined) f.generatedOptions = null; } catch (e) {}
        try { f.setValue(value); } catch (e) {}
      }
      // PROC first (its validator re-picks FUNC), then FUNC (its
      // validator re-picks OUTPUT), then OUTPUT — saved value wins.
      // If the stashed FUNC isn't defined under the stashed PROC (the
      // function was moved / the proc renamed since that save), the
      // registry knows its real home — apply THAT as PROC instead, so
      // the FUNC value isn't rejected against the wrong proc's list.
      var procToApply = sel.proc;
      if (sel.func) {
        var owner = (global._mfFuncRegistry || []).filter(function (f) {
          return String(f.name || "") === String(sel.func);
        })[0];
        if (owner && owner.proc && String(owner.proc) !== String(sel.proc || "")) {
          procToApply = String(owner.proc);
        }
      }
      setField("PROC", procToApply);
      setField("FUNC", sel.func);
      setField("OUTPUT", sel.output);
    });
  };

  global.mfBindWorkspace = function (workspace) {
    workspace.addChangeListener(function () { global.mfScanFuncs(workspace); });
    var div = document.getElementById("blocklyDiv");
    if (!div || div._mfBound) return;
    div._mfBound = true;
    div.addEventListener("dblclick", function (ev) {
      var el = ev.target;
      var blockEl = el && el.closest ? el.closest("[data-id]") : null;
      var id = blockEl && blockEl.getAttribute("data-id");
      var block = id && workspace.getBlockById(id);
      if (!block) return;
      if (block.type === "mf_display_widget") { openWidgetComposer(block); return; }
      if (String(block.type).indexOf("mf_get_") === 0) {
        var f = block.getField("ID");
        if (f && f.showEditor_) f.showEditor_();
      }
    });
  };
})(window);

// ═══════════════════════════════════════════════════════════════
// Type-colour overrides for built-in blocks: a block that returns
// a Number/Boolean gets the Number/Boolean colour, not the stock
// Lists purple (e.g. length of [list] returns a number).
// ═══════════════════════════════════════════════════════════════
(function () {
  var overrides = { lists_length: 230, lists_isEmpty: 210, lists_indexOf: 230 };
  for (var name in overrides) {
    var def = Blockly.Blocks[name];
    if (!def || !def.init) continue;
    (function (origInit, colour) {
      def.init = function () { origInit.call(this); this.setColour(colour); };
    })(def.init, overrides[name]);
  }
})();

// ═══════════════════════════════════════════════════════════════
// MF action icons — the screen picker (pipette) and the resolution
// auto-fill (arrow). Both reuse the mutator-gear chrome from the vendored
// lib/blockly_action_icons.js (themed .blocklyIconShape/.blocklyIconSymbol,
// hover + dim handled by Blockly CSS), falling back to a plain badge if the
// lib is missing. Clicking pipette opens the F2 "pick from screen" popup
// (window.MFPicker), clicking arrow fills the current monitor resolution
// (window.MFGet).
(function (global) {
  var B = Blockly;
  if (!B || !B.icons || !B.icons.Icon || !B.icons.IconType) return;

  var MF_PICKER_TYPE = new B.icons.IconType("mf_picker");
  var MF_GET_TYPE = new B.icons.IconType("mf_get");
  var AI = B.actionIcons;

  function drawPickerChrome(svgRoot) {
    var dom = B.utils.dom, Svg = B.utils.Svg;
    if (AI && AI.drawChrome && AI.drawPickerSymbol) {
      AI.drawChrome(svgRoot);
      AI.drawPickerSymbol(svgRoot);
      return;
    }
    // fallback: plain badge + crosshair (pre-refactor look)
    dom.createSvgElement(Svg.RECT, {
      "class": "blocklyIconShape", rx: "4", ry: "4", height: "16", width: "16",
    }, svgRoot);
    var g = dom.createSvgElement(Svg.G, { "class": "blocklyIconSymbol" }, svgRoot);
    var mkLine = function (x1, y1, x2, y2) {
      return dom.createSvgElement(Svg.LINE, {
        x1: x1, y1: y1, x2: x2, y2: y2,
        "stroke-width": "1.4", "stroke-linecap": "round",
      }, g);
    };
    mkLine(8, 2.6, 8, 5.2); mkLine(8, 10.8, 8, 13.4);
    mkLine(2.6, 8, 5.2, 8); mkLine(10.8, 8, 13.4, 8);
    dom.createSvgElement(Svg.CIRCLE, {
      cx: "8", cy: "8", r: "2.4", fill: "none", "stroke-width": "1.4",
    }, g);
  }

  function drawMetaChrome(svgRoot) {
    var dom = B.utils.dom, Svg = B.utils.Svg;
    if (AI && AI.drawChrome) {
      AI.drawChrome(svgRoot);
    } else {
      dom.createSvgElement(Svg.RECT, {
        "class": "blocklyIconShape", rx: "4", ry: "4", height: "16", width: "16",
      }, svgRoot);
    }
    // corner brackets + center dot — "locate the picked region"
    var g = dom.createSvgElement(Svg.G, { "class": "blocklyIconSymbol" }, svgRoot);
    var path = dom.createSvgElement(Svg.PATH, {
      "class": "blocklyIconSymbol", fill: "none", "stroke-width": "1.4",
      "stroke-linecap": "round",
      d: "M2.6 5.4 V2.9 H5.2 M10.8 2.9 h2.6 v2.5 M13.4 10.6 v2.5 h-2.6 M5.2 13.1 H2.6 v-2.5",
    }, svgRoot);
    dom.createSvgElement(Svg.CIRCLE, {
      "class": "blocklyIconSymbol", cx: "8", cy: "8", r: "1.7",
    }, svgRoot);
  }

  function drawGetChrome(svgRoot) {
    var dom = B.utils.dom, Svg = B.utils.Svg;
    if (AI && AI.drawChrome && AI.drawGetSymbol) {
      AI.drawChrome(svgRoot);
      AI.drawGetSymbol(svgRoot);
      return;
    }
    dom.createSvgElement(Svg.RECT, {
      "class": "blocklyIconShape", rx: "4", ry: "4", height: "16", width: "16",
    }, svgRoot);
    // fallback arrow
    dom.createSvgElement(Svg.PATH, {
      "class": "blocklyIconSymbol",
      d: "M9.7 2.5 h2.6 v8.35 H6.05 v2.2 L2.2 10.25 L6.05 5.95 v2.2 H9.7 Z",
    }, svgRoot);
  }

  class MFActionIcon extends B.icons.Icon {
    getSize() { return new B.utils.Size(17, 17); }
    isClickableInFlyout() { return false; }
    getWeight() { return 2; }
  }

  class MFPickIcon extends MFActionIcon {
    constructor(mode, sourceBlock) {
      super(sourceBlock);
      this._mfMode = mode || "point";
    }
    getType() { return MF_PICKER_TYPE; }
    initView(pointerdownListener) {
      if (this.svgRoot) return;
      B.icons.Icon.prototype.initView.call(this, pointerdownListener);
      drawPickerChrome(this.svgRoot);
      if (this.setTooltip) this.setTooltip(this._mfMode === "file" ? "Browse for a file" : "Pick from screen (F2)");
    }
    onClick() {
      var block = this.sourceBlock;
      if (!block || block.isInFlyout) return;
      if (this._mfMode === "file") {
        if (global.MFFileDialog && typeof global.MFFileDialog.request === "function") {
          global.MFFileDialog.request(block);
        }
        return;
      }
      if (this._mfMode === "res_image") {
        if (global.MFResImage && typeof global.MFResImage.request === "function") {
          global.MFResImage.request(block);
        }
        return;
      }
      if (this._mfMode === "color") {
        if (global.MFColorPick && typeof global.MFColorPick.request === "function") {
          global.MFColorPick.request(block);
        }
        return;
      }
      if (global.MFPicker && typeof global.MFPicker.requestPick === "function") {
        global.MFPicker.requestPick(block, this._mfMode);
      }
    }
  }

  class MFGetIcon extends MFActionIcon {
    constructor(target, sourceBlock) {
      super(sourceBlock);
      this._mfTarget = target || "ratio"; // which socket to fill
    }
    getType() { return MF_GET_TYPE; }
    initView(pointerdownListener) {
      if (this.svgRoot) return;
      B.icons.Icon.prototype.initView.call(this, pointerdownListener);
      drawGetChrome(this.svgRoot);
      if (this.setTooltip) this.setTooltip("Apply current monitor resolution");
    }
    onClick() {
      var block = this.sourceBlock;
      if (!block || block.isInFlyout) return;
      if (global.MFGet && typeof global.MFGet.request === "function") {
        global.MFGet.request(block, this._mfTarget);
      }
    }
  }

  // ── meta-drop icon: reads the image's pick metadata and drops the
  // picked region back into the editor as point + box blocks ─────────
  var MF_META_DROP_TYPE = new B.icons.IconType("mf_meta_drop");

  class MFMetaDropIcon extends MFActionIcon {
    // no mode arg — the picker takes ('res_image', this), but this icon
    // inherits Icon's (sourceBlock) constructor; passing a mode string
    // first made sourceBlock a STRING and crashed the flyout render.
    constructor(sourceBlock) { super(sourceBlock); }
    getType() { return MF_META_DROP_TYPE; }
    initView(pointerdownListener) {
      if (this.svgRoot) return;
      B.icons.Icon.prototype.initView.call(this, pointerdownListener);
      drawMetaChrome(this.svgRoot);
      if (this.setTooltip) this.setTooltip("Drop the picked region as point + box blocks");
    }
    onClick() {
      var block = this.sourceBlock;
      if (!block || block.isInFlyout) return;
      if (global.MFMetaDrop && typeof global.MFMetaDrop.request === "function") {
        global.MFMetaDrop.request(block);
      }
    }
  }

  B.icons.MFPickIcon = MFPickIcon;
  B.icons.MF_PICKER_TYPE = MF_PICKER_TYPE;
  B.icons.MFGetIcon = MFGetIcon;
  B.icons.MF_GET_TYPE = MF_GET_TYPE;
  B.icons.MFMetaDropIcon = MFMetaDropIcon;
  B.icons.MF_META_DROP_TYPE = MF_META_DROP_TYPE;
})(typeof window !== "undefined" ? window : this);

// ═══════════════════════════════════════════════════════════════
// MFMetaDrop — the image block's "get" icon handler. Reads the pick
// metadata sidecar for the block's image (saved by the pipette when
// the crop was taken) and drops a point block + a box block with the
// picked region into the workspace — unconnected, ready to wire.
// ═══════════════════════════════════════════════════════════════
(function (global) {
  "use strict";

  function mfmtToast(msg) {
    try {
      var t = document.getElementById("mf-meta-toast");
      if (!t) {
        t = document.createElement("div");
        t.id = "mf-meta-toast";
        t.style.cssText = "position:fixed;left:50%;top:14px;transform:translateX(-50%);" +
          "background:#2d2d3a;color:#e8e8f0;padding:7px 14px;border-radius:8px;" +
          "font:12px 'Segoe UI',sans-serif;z-index:99999;pointer-events:none;" +
          "box-shadow:0 2px 10px rgba(0,0,0,.45);opacity:0;transition:opacity .18s";
        document.body.appendChild(t);
      }
      t.textContent = msg;
      t.style.opacity = "1";
      clearTimeout(t._h);
      t._h = setTimeout(function () { t.style.opacity = "0"; }, 2200);
    } catch (e) {}
  }

  // set a number on an input socket (creates the math_number child)
  function mfmtSetNum(block, inputName, v) {
    var input = block.getInput(inputName);
    if (!input || !input.connection) return false;
    var child = input.connection.targetBlock();
    if (child) { try { child.dispose(); } catch (e) {} }
    var n = block.workspace.newBlock("math_number");
    n.setFieldValue(String(v), "NUM");
    try { n.initSvg(); } catch (e) {}
    n.outputConnection.connect(input.connection);
    return true;
  }

  // drop a pcr_point_xy + pcr_box_xyxy with the picked region next to the
  // block — unconnected, just sitting there ready to wire.
  // Built via XML + domToWorkspace (not hand-rolled newBlock/initSvg):
  // that's the path that fully renders the number children — manual
  // assembly left them unrendered and the sockets looked blank.
  function mfmtDrop(block, meta) {
    var ws = block.workspace;
    var bx = meta.box || [];
    var pt = meta.point || [bx[0] || 0, bx[1] || 0];
    var rel = { x: 0, y: 0 };
    try { var r = block.getRelativeToSurfaceXY(); rel = { x: r.x, y: r.y }; } catch (e) {}
    var height = 90;
    try { height = (block.getHeightWidth && block.getHeightWidth().height) || 90; } catch (e) {}

    var esc = function (v) {
      return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    };
    var num = function (name, v) {
      return '<value name="' + name + '"><block type="math_number">' +
             '<field name="NUM">' + esc(v) + '</field></block></value>';
    };
    var x1 = Math.round(rel.x + 16);
    var y1 = Math.round(rel.y + height + 24);
    var xml =
      '<xml>' +
        '<block type="pcr_point_xy" x="' + x1 + '" y="' + y1 + '">' +
          num("X", pt[0]) + num("Y", pt[1]) +
        '</block>' +
        '<block type="pcr_box_xyxy" x="' + x1 + '" y="' + (y1 + 84) + '">' +
          num("X1", bx[0]) + num("Y1", bx[1]) + num("X2", bx[2]) + num("Y2", bx[3]) +
        '</block>' +
      '</xml>';
    var doc = null;
    try { doc = new DOMParser().parseFromString(xml, "text/xml"); } catch (e) {}
    if (!doc) return { point: null, box: null };
    var prev = {};
    ws.getTopBlocks(false).forEach(function (b) { prev[b.id] = 1; });
    var ids = [];
    try { ids = (global.Blockly || window.Blockly).Xml.domToWorkspace(doc.documentElement, ws) || []; } catch (e) { ids = []; }
    var fresh = ws.getTopBlocks(false).filter(function (b) { return !prev[b.id]; });
    var point = null, box = null;
    (ids.length ? ids.map(function (id) { return ws.getBlockById(id); })
                : fresh).forEach(function (b) {
      if (!b) return;
      if (b.type === "pcr_point_xy" && !point) point = b;
      if (b.type === "pcr_box_xyxy" && !box) box = b;
    });
    return { point: point, box: box };
  }

  function mfmtPathOf(block) {
    if (typeof block.mfPathText === "function") return String(block.mfPathText() || "");
    try {
      var input = block.getInput("PATH");
      if (input && input.connection) {
        var child = input.connection.targetBlock();
        if (child && child.type === "text") return String(child.getFieldValue("TEXT") || "");
      }
    } catch (e) {}
    return "";
  }

  // ── where a block's pick metadata lives ─────────────────────────
  // mfmtResolve walks a block (and its wired PATH chain) and returns
  //   { setting: "<setting id>" }  — an image/resloc mode-settings block
  //   { res: "<res:// or path>" }  — a concrete resource location
  //   null                        — nothing resolvable on this block
  function mfmtResolve(block, depth) {
    depth = depth || 0;
    if (!block || depth > 6) return null;
    try {
      if (typeof block.mfMetaSource === "function") {
        var s = block.mfMetaSource();
        if (s && s.setting) return { setting: s.setting };
      }
    } catch (e) {}
    var path = mfmtPathOf(block);
    if (path) return { res: path };
    try {
      var input = block.getInput("PATH");
      if (input && input.connection) {
        var child = input.connection.targetBlock();
        if (child && child !== block) {
          var r = mfmtResolve(child, depth + 1);
          if (r) return r;
        }
      }
    } catch (e) {}
    return null;
  }

  // fetch the metadata embedded in a resource PNG (tEXt "mfmeta")
  function mfmtFetchMetaByRes(res) {
    var url;
    if (res.indexOf("res://") === 0) {
      var name = res.slice("res://".length);
      var wsId = global._mfWorkspaceId || "";
      url = "/blockly/resource_meta?ws=" + encodeURIComponent(wsId) +
            "&res=" + encodeURIComponent(name);
    } else {
      url = "/me/api/image_meta?path=" + encodeURIComponent(res);
    }
    return fetch(url).then(function (r) { return r.json(); }).catch(function () { return null; });
  }

  // mode-settings mapping entry for a setting id (may be stale — the
  // editor refreshes it on registry broadcasts)
  function mfmtEntryForSetting(id) {
    var items = (global._mfMappings && global._mfMappings.settings) || [];
    var entry = null;
    items.forEach(function (it) { if (it && it.id === id && !entry) entry = it; });
    return entry;
  }

  // {box, point, res} out of a mapping entry:
  // live picked value first ({res, box, point} of the active mode),
  // then the builder-default box/point, else just the res.
  function mfmtMetaFromEntry(entry) {
    if (!entry) return null;
    var box = null, point = null, res = "";
    if (entry.live) {
      res = String(entry.live.res || "");
      if (entry.live.box && entry.live.box.length === 4) {
        box = entry.live.box;
        point = (entry.live.point && entry.live.point.length === 2)
          ? entry.live.point : [box[0], box[1]];
      }
    }
    if (!box && entry.box && entry.box.length === 4) {
      box = entry.box;
      point = (entry.point && entry.point.length === 2) ? entry.point : [box[0], box[1]];
    }
    if (!box) res = res || String(entry.value || "");
    return { box: box, point: point, res: res };
  }

  // ask the dashboard parent for a FRESH mapping entry (mode-settings
  // values change without a registry broadcast) — resolves to an entry
  // or null after ~1.5s
  function mfmtQueryParent(setting) {
    return new Promise(function (resolve) {
      var reqId = "mfmeta_" + Date.now() + "_" + Math.random().toString(36).slice(2);
      var onMsg = function (ev) {
        var d = ev.data;
        if (!d || d.type !== "mf_meta_result" || d.reqId !== reqId) return;
        window.removeEventListener("message", onMsg);
        resolve(d.entry || null);
      };
      window.addEventListener("message", onMsg);
      try {
        window.parent.postMessage({ type: "mf_meta_query", reqId: reqId, setting: setting }, "*");
      } catch (e) {
        window.removeEventListener("message", onMsg);
        resolve(null);
        return;
      }
      setTimeout(function () { window.removeEventListener("message", onMsg); resolve(null); }, 1500);
    });
  }

  function mfmtApplyMeta(block, meta, label) {
    if (!meta || !meta.box) {
      mfmtToast("No pick metadata" + (label ? " for '" + label + "'" : "") +
                " — pick the image with F2 first");
      return;
    }
    mfmtDrop(block, meta);
    mfmtToast("Dropped point (" + meta.point[0] + ", " + meta.point[1] + ") + box " +
      (meta.box[2] - meta.box[0]) + "x" + (meta.box[3] - meta.box[1]));
  }

  // settings-block path: mapping entry (live value → builder default →
  // PNG's embedded mfmeta as last resort)
  function mfmtFromSetting(block, id) {
    if (!id) { mfmtToast("Choose a setting on the block first"); return; }
    var entry = mfmtEntryForSetting(id);
    var meta = mfmtMetaFromEntry(entry);
    var finish = function (ent) {
      var m = mfmtMetaFromEntry(ent);
      if (m && m.box) { mfmtApplyMeta(block, m, id); return; }
      var res = (m && m.res) || "";
      if (res) {
        mfmtFetchMetaByRes(res).then(function (d) {
          if (d && d.ok && d.meta && d.meta.box) mfmtApplyMeta(block, d.meta, id);
          else mfmtApplyMeta(block, null, id);
        });
        return;
      }
      mfmtApplyMeta(block, null, id);
    };
    if (meta && meta.box) { finish(entry); return; }   // mappings fresh enough
    mfmtQueryParent(id).then(function (fresh) { finish(fresh || entry); });
  }

  global.MFMetaDrop = {
    // the icon's entry point — reads the pick metadata for whatever the
    // block points at: a mode-settings image, a res:// resource, a path.
    request: function (block) {
      var src = mfmtResolve(block);
      if (!src) { mfmtToast("The block has no resource location yet"); return; }
      if (src.setting) { mfmtFromSetting(block, src.setting); return; }
      var path = src.res;
      mfmtFetchMetaByRes(path).then(function (d) {
        if (!d || !d.ok) { mfmtToast("Server unreachable"); return; }
        if (!d.meta || !d.meta.box) {
          mfmtToast("No pick metadata for this image — re-pick it with the pipette (F2)");
          return;
        }
        mfmtApplyMeta(block, d.meta);
      });
    },
    // exposed for tests / power users: drop with explicit metadata
    drop: mfmtDrop,
    toast: mfmtToast,
  };
})(typeof window !== "undefined" ? window : this);
