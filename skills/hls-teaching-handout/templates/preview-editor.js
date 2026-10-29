"use strict";

const FONT_SIZES = ["9.5", "10", "10.5", "11", "11.5", "12", "13", "14", "16", "18", "20", "24", "28"];
const MIN_BODY_FONT_SIZE = 10.5;
const MANUAL_PAGE_BREAK_ATTR = "data-manual-page-break";
const EDITABLE_SELECTOR = [
  ".cover-kicker", ".cover-title", ".cover-subtitle", ".cover-topics",
  ".chapter-title", ".section h2", ".section h3", "p", "li", "th", "td",
  ".box-label", ".example-label", "figcaption", ".document-note"
].join(",");
const LOCKED_SELECTOR = ".contents-page, thead, header, footer, [data-locked-region], [data-editor-locked]";

const frame = document.querySelector("#document-frame");
const statusBox = document.querySelector("#editor-status");
const toolbar = document.querySelector("#hls-editor-toolbar");
const sizeSelect = toolbar.querySelector('[data-tool="font-size"]');
let initialHTML = "";
let activeDocument = null;
let savedRange = null;
const HISTORY_LIMIT = 100;
let undoStack = [];
let redoStack = [];
let restoringHistory = false;

for (const size of FONT_SIZES) {
  const option = document.createElement("option");
  option.value = size;
  option.textContent = `${size}pt`;
  if (size === "11") option.selected = true;
  sizeSelect.append(option);
}

function setStatus(message, state = "working") {
  statusBox.textContent = message;
  statusBox.dataset.state = state;
}

function splitProtectedHeading(heading) {
  if (heading.querySelector("[data-editor-title]")) return;
  const match = heading.textContent.match(/^((?:第[^　\s]+章|\d+(?:\.\d+){0,2})[　\s]+)([\s\S]+)$/);
  if (!match) return;
  heading.textContent = "";
  const number = activeDocument.createElement("span");
  number.dataset.editorNumber = "true";
  number.contentEditable = "false";
  number.textContent = match[1];
  const title = activeDocument.createElement("span");
  title.dataset.editorTitle = "true";
  title.contentEditable = "true";
  title.textContent = match[2];
  heading.append(number, title);
}

function isLocked(node) {
  const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  if (!element) return true;
  if (element.closest(".document-note")) return false;
  if (element.closest("th, td")) return false;
  if (element.closest(".contents-page")) return true;
  if (element.closest("thead") && !element.closest("th")) return true;
  if (element.matches("table, thead, tbody, tr")) return true;
  return Boolean(element.closest(LOCKED_SELECTOR) && !element.matches(".cover-kicker, .cover-title, .cover-subtitle, .cover-topics"));
}

function configureEditing() {
  activeDocument = frame.contentDocument;
  savedRange = null;
  activeDocument.querySelectorAll("[contenteditable]").forEach((node) => node.removeAttribute("contenteditable"));
  activeDocument.querySelectorAll(".chapter-title, .section h2, .section h3").forEach(splitProtectedHeading);
  activeDocument.querySelectorAll(EDITABLE_SELECTOR).forEach((node) => {
    if (!isLocked(node) && !node.matches(".chapter-title, .section h2, .section h3")) node.contentEditable = "true";
  });
  activeDocument.querySelectorAll("[data-editor-title]").forEach((node) => { node.contentEditable = "true"; });
  activeDocument.querySelectorAll(".contents-page, table, thead, tbody, tr, [data-locked-region]").forEach((node) => {
    node.dataset.editorLocked = "true";
  });
  restoringHistory = false;

  activeDocument.addEventListener("beforeinput", (event) => {
    const selection = activeDocument.defaultView.getSelection();
    const anchor = selection && selection.anchorNode;
    if (!anchor || isLocked(anchor) || anchor.parentElement?.matches("[data-editor-number]")) {
      event.preventDefault();
      return;
    }
    if (event.inputType !== "historyUndo" && event.inputType !== "historyRedo" && event.inputType !== "insertFromPaste") {
      recordHistory();
    }
  });
  activeDocument.addEventListener("paste", handlePaste);
  activeDocument.addEventListener("selectionchange", () => {
    const selection = activeDocument.defaultView.getSelection();
    if (!selection || !selection.rangeCount || !selection.anchorNode || isLocked(selection.anchorNode)) return;
    savedRange = selection.getRangeAt(0).cloneRange();
  });
  activeDocument.addEventListener("click", (event) => {
    const link = event.target.closest(".toc a");
    if (!link) return;
    event.preventDefault();
    activeDocument.querySelector(link.getAttribute("href"))?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  const height = Math.max(activeDocument.documentElement.scrollHeight + 24, 900);
  frame.style.height = `${height}px`;
  setStatus("可修改正文、表头、表题/图题、来源说明和基础排版；目录、封面背景、页眉页脚及表格结构已锁定。", "ready");
}

function sanitizePasteHTML(source) {
  const parsed = new DOMParser().parseFromString(source, "text/html");
  const allowed = new Set(["P", "BR", "STRONG", "B"]);
  function clean(node) {
    if (node.nodeType === Node.TEXT_NODE) return activeDocument.createTextNode(node.textContent);
    if (node.nodeType !== Node.ELEMENT_NODE) return activeDocument.createDocumentFragment();
    const fragment = activeDocument.createDocumentFragment();
    const target = allowed.has(node.tagName)
      ? activeDocument.createElement(node.tagName === "B" ? "strong" : node.tagName.toLowerCase())
      : fragment;
    for (const child of node.childNodes) target.append(clean(child));
    return target;
  }
  const container = activeDocument.createElement("div");
  for (const child of parsed.body.childNodes) container.append(clean(child));
  return container.innerHTML;
}

function handlePaste(event) {
  const selection = activeDocument.defaultView.getSelection();
  if (!selection?.anchorNode || isLocked(selection.anchorNode)) {
    event.preventDefault();
    return;
  }
  event.preventDefault();
  recordHistory();
  const rich = event.clipboardData.getData("text/html");
  if (rich) {
    activeDocument.execCommand("insertHTML", false, sanitizePasteHTML(rich));
  } else {
    activeDocument.execCommand("insertText", false, event.clipboardData.getData("text/plain"));
  }
}

function restoreSelection() {
  if (!savedRange || !activeDocument) return;
  const selection = activeDocument.defaultView.getSelection();
  selection.removeAllRanges();
  selection.addRange(savedRange);
}

function selectionBlock() {
  const selection = activeDocument?.defaultView.getSelection();
  const node = selection?.anchorNode;
  if (!node) return null;
  return (node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement)?.closest(
    "[data-editor-title], .cover-kicker, .cover-title, .cover-subtitle, .cover-topics, p, li, th, td, h2, h3, figcaption, .document-note"
  ) || null;
}

function serializeDocument() {
  return `<!doctype html>\n${activeDocument.documentElement.outerHTML}`;
}

function recordHistory() {
  if (!activeDocument || restoringHistory) return;
  const snapshot = serializeDocument();
  if (undoStack[undoStack.length - 1] !== snapshot) {
    undoStack.push(snapshot);
    if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
  }
  redoStack = [];
}

function restoreHistory(snapshot) {
  if (!snapshot) return;
  restoringHistory = true;
  frame.srcdoc = snapshot;
}

function undoEdit() {
  if (!undoStack.length) {
    setStatus("没有可撤销的操作。", "ready");
    return;
  }
  redoStack.push(serializeDocument());
  restoreHistory(undoStack.pop());
  setStatus("已撤销上一步操作。", "editing");
}

function redoEdit() {
  if (!redoStack.length) {
    setStatus("没有可重做的操作。", "ready");
    return;
  }
  undoStack.push(serializeDocument());
  restoreHistory(redoStack.pop());
  setStatus("已重做上一步操作。", "editing");
}

async function saveDocument() {
  const response = await fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html: serializeDocument() }),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "保存失败");
  return result;
}

async function approveDocument() {
  setStatus("正在保存并检查锁定结构……");
  await saveDocument();
  const response = await fetch("/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html: serializeDocument() }),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "确认失败");
  setStatus("已确认，正在生成 PDF 与执行 QA……");
  pollStatus();
}

async function pollStatus() {
  const response = await fetch("/status", { cache: "no-store" });
  const result = await response.json();
  if (result.state === "failed") {
    setStatus(`生成失败：${result.error}`, "error");
    return;
  }
  if (result.state === "complete") {
    setStatus(`生成完成。PDF：${result.pdf || "已生成"}；QA：${result.qa || "已完成"}`, "complete");
    return;
  }
  if (result.state === "approved") {
    setStatus("内容已确认；当前示例未配置自动渲染命令。", "complete");
    return;
  }
  setStatus(result.state === "rendering" ? "正在生成 PDF 与执行 QA……" : "等待确认……");
  setTimeout(pollStatus, 800);
}

toolbar.addEventListener("mousedown", (event) => {
  if (event.target.closest("button[data-tool]")) event.preventDefault();
});

toolbar.addEventListener("click", async (event) => {
  const control = event.target.closest("[data-tool]");
  if (!control || control.tagName === "SELECT") return;
  const tool = control.dataset.tool;
  try {
    restoreSelection();
    if (tool === "undo") {
      undoEdit();
    } else if (tool === "redo") {
      redoEdit();
    } else if (tool === "bold") {
      recordHistory();
      const selection = activeDocument.defaultView.getSelection();
      if (selection && !selection.isCollapsed) {
        activeDocument.execCommand("bold", false);
      } else {
        const block = selectionBlock();
        if (!block) throw new Error("请先把光标放在正文中");
        const enabled = block.dataset.fontWeight !== "bold";
        block.dataset.fontWeight = enabled ? "bold" : "";
        block.style.fontWeight = enabled ? "700" : "";
      }
    } else if (tool.startsWith("align-")) {
      const block = selectionBlock();
      if (block) {
        recordHistory();
        block.dataset.textAlign = tool.replace("align-", "");
      }
    } else if (tool === "page-break") {
      const block = selectionBlock();
      if (!block) throw new Error("请先把光标放在正文中");
      recordHistory();
      const marker = activeDocument.createElement("div");
      marker.className = "manual-page-break";
      marker.setAttribute(MANUAL_PAGE_BREAK_ATTR, "true");
      marker.contentEditable = "false";
      block.insertAdjacentElement("afterend", marker);
    } else if (tool === "reset") {
      recordHistory();
      frame.srcdoc = initialHTML;
    } else if (tool === "approve") {
      await approveDocument();
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
});

toolbar.addEventListener("change", (event) => {
  const control = event.target.closest("select[data-tool]");
  if (!control) return;
  restoreSelection();
  const block = selectionBlock();
  if (!block) {
    setStatus("请先选择要调整的文字。", "error");
    return;
  }
  if (control.dataset.tool === "font-size") {
    const value = Number(control.value);
    const isBody = block.matches("p, li, td");
    if (isBody && value < MIN_BODY_FONT_SIZE) {
      setStatus("普通正文不得小于 10.5pt。", "error");
      return;
    }
    recordHistory();
    block.dataset.fontSize = control.value;
  } else if (control.dataset.tool === "line-height") {
    recordHistory();
    block.dataset.lineHeight = control.value;
  } else if (control.dataset.tool === "block-type") {
    if (block.closest(".cover") || block.matches("th, td, [data-editor-title]")) {
      setStatus("当前内容不能更改段落类型。", "error");
      return;
    }
    recordHistory();
    activeDocument.execCommand("formatBlock", false, control.value);
  }
});

async function loadDocument() {
  const response = await fetch("/document", { cache: "no-store" });
  if (!response.ok) throw new Error("无法读取待编辑讲义");
  initialHTML = await response.text();
  undoStack = [];
  redoStack = [];
  restoringHistory = false;
  frame.addEventListener("load", configureEditing);
  frame.srcdoc = initialHTML;
}

loadDocument().catch((error) => setStatus(error.message, "error"));
