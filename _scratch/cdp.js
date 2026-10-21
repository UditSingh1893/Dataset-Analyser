// Record every network request Chrome makes while loading a page, using the
// DevTools Protocol. Prints request URLs and response bodies that mention
// "claude" or "contributor".
const { spawn } = require("child_process");
const http = require("http");
const os = require("os");
const path = require("path");
const fs = require("fs");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const URL_TO_LOAD = process.argv[2];
const PORT = 9333;

function get(url) {
  return new Promise((res, rej) => {
    http.get(url, (r) => {
      let d = "";
      r.on("data", (c) => (d += c));
      r.on("end", () => res(d));
    }).on("error", rej);
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "cdp_"));
  const chrome = spawn(CHROME, [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    "about:blank",
  ], { stdio: "ignore" });

  let target = null;
  for (let i = 0; i < 40; i++) {
    await sleep(500);
    try {
      const list = JSON.parse(await get(`http://127.0.0.1:${PORT}/json/list`));
      target = list.find((t) => t.type === "page");
      if (target) break;
    } catch (_) {}
  }
  if (!target) {
    console.error("could not attach to Chrome");
    chrome.kill();
    process.exit(1);
  }

  const WebSocket = require("ws");
  const ws = new WebSocket(target.webSocketDebuggerUrl, { perMessageDeflate: false });
  let id = 0;
  const pending = new Map();
  const send = (method, params = {}, sessionId) =>
    new Promise((resolve) => {
      const msgId = ++id;
      pending.set(msgId, resolve);
      ws.send(JSON.stringify({ id: msgId, method, params, sessionId }));
    });

  const interesting = [];

  ws.on("message", async (raw) => {
    const msg = JSON.parse(raw);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg.result);
      pending.delete(msg.id);
      return;
    }
    if (msg.method === "Network.responseReceived") {
      const { requestId, response } = msg.params;
      interesting.push({ requestId, url: response.url, status: response.status });
    }
  });

  await new Promise((r) => ws.on("open", r));
  await send("Network.enable");
  await send("Page.enable");
  await send("Page.navigate", { url: URL_TO_LOAD });
  await sleep(12000);

  console.log("--- responses mentioning claude/contributor ---");
  for (const r of interesting) {
    if (!/claude|contributor/i.test(r.url)) continue;
    let body = "";
    try {
      const res = await send("Network.getResponseBody", { requestId: r.requestId });
      body = res.body || "";
    } catch (e) {
      body = "<no body>";
    }
    const hit = /claude/i.test(body);
    console.log(`\nURL: ${r.url}\n  status=${r.status} len=${body.length} claude=${hit}`);
    if (hit) {
      const m = body.match(/.{200}claude.{300}/i);
      if (m) console.log("  SNIPPET: " + m[0].replace(/\s+/g, " "));
    }
  }

  console.log("\n--- all response urls (github only) ---");
  for (const r of interesting) {
    if (r.url.includes("github.com") && !r.url.includes("githubassets"))
      console.log("  " + r.url);
  }

  ws.close();
  chrome.kill();
  process.exit(0);
})();
