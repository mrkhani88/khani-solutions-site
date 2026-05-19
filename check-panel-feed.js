#!/usr/bin/env node

const { mkdtemp, rm } = require("node:fs/promises");
const { tmpdir } = require("node:os");
const { join } = require("node:path");
const { spawn } = require("node:child_process");

const targetUrl = process.argv[2] || "http://127.0.0.1:4178/";
const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const port = 9300 + Math.floor(Math.random() * 500);

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed ${response.status}: ${url}`);
  return response.json();
}

async function waitForPageTarget() {
  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    try {
      const targets = await fetchJson(`http://127.0.0.1:${port}/json/list`);
      const page = targets.find((target) => target.type === "page");
      if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch {
      await wait(150);
    }
  }
  throw new Error("Chrome DevTools target did not become available.");
}

function createClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  let id = 0;
  const pending = new Map();

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id) return;
    const request = pending.get(message.id);
    if (!request) return;
    pending.delete(message.id);
    if (message.error) {
      request.reject(new Error(message.error.message));
    } else {
      request.resolve(message.result);
    }
  });

  return new Promise((resolve, reject) => {
    socket.addEventListener("open", () => {
      resolve({
        send(method, params = {}) {
          const requestId = ++id;
          socket.send(JSON.stringify({ id: requestId, method, params }));
          return new Promise((requestResolve, requestReject) => {
            pending.set(requestId, { resolve: requestResolve, reject: requestReject });
          });
        },
        close() {
          socket.close();
        },
      });
    });
    socket.addEventListener("error", () => reject(new Error("WebSocket connection failed.")), { once: true });
  });
}

async function evaluate(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Browser evaluation failed.");
  }
  return result.result.value;
}

async function navigateAndWait(client, url) {
  await client.send("Page.navigate", { url });
  const startedAt = Date.now();
  let introMetrics = null;
  while (Date.now() - startedAt < 3000) {
    await wait(100);
    introMetrics = await evaluate(
      client,
      `(() => {
        const logo = document.querySelector("[data-intro-logo]");
        const loader = document.querySelector("[data-intro-loader]");
        if (!logo) return null;
        const styles = getComputedStyle(logo);
        return {
          width: parseFloat(styles.width),
          height: parseFloat(styles.height),
          maxSize: Math.min(window.innerWidth, window.innerHeight),
          backdropColor: loader ? getComputedStyle(loader).backgroundColor : "",
        };
      })()`,
    );
    if (introMetrics?.width > 0 && introMetrics?.height > 0) break;
  }

  if (
    introMetrics &&
    (introMetrics.width > introMetrics.maxSize ||
      introMetrics.height > introMetrics.maxSize ||
      introMetrics.width < introMetrics.maxSize - 40 ||
      introMetrics.height < introMetrics.maxSize - 40)
  ) {
    throw new Error(`intro logo does not start near shortest panel side (${introMetrics.width}x${introMetrics.height} vs ${introMetrics.maxSize}).`);
  }
  if (introMetrics && !introMetrics.backdropColor.includes("255, 255, 255")) {
    throw new Error(`intro backdrop is not logo-matched white (${introMetrics.backdropColor}).`);
  }

  while (Date.now() - startedAt < 5500) {
    const introDone = await evaluate(
      client,
      `(() => {
        const loader = document.querySelector("[data-intro-loader]");
        return !document.body.classList.contains("is-intro-running") && (loader?.classList.contains("is-done") ?? true);
      })()`,
    );
    if (introDone) return;
    await wait(120);
  }
}

async function waitForFounderPhoto(client, viewportName) {
  const startedAt = Date.now();
  let imageState = null;

  while (Date.now() - startedAt < 10000) {
    imageState = await evaluate(
      client,
      `(() => {
        const image = document.querySelector(".contact-profile img");
        if (!image) return null;
        if (window.centerFocalImages) window.centerFocalImages();
        return {
          src: image.getAttribute("src"),
          complete: image.complete,
          naturalWidth: image.naturalWidth,
          naturalHeight: image.naturalHeight,
          focalReady: image.dataset.focalReady,
        };
      })()`,
    );

    if (
      imageState?.complete &&
      imageState.naturalWidth === 2085 &&
      imageState.naturalHeight === 3783 &&
      imageState.focalReady === "true"
    ) {
      return;
    }

    await wait(180);
  }

  throw new Error(`${viewportName}: founder photo did not finish loading ${JSON.stringify(imageState)}.`);
}

async function checkViewport(client, viewport) {
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: viewport.mobile ? 2 : 1,
    mobile: viewport.mobile,
  });
  await client.send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "no-preference" }],
  });
  await client.send("Emulation.setTouchEmulationEnabled", { enabled: viewport.mobile });
  await navigateAndWait(client, `${targetUrl}${targetUrl.includes("?") ? "&" : "?"}check=${Date.now()}-${viewport.name}`);
  await waitForFounderPhoto(client, viewport.name);

  const metrics = await evaluate(
    client,
    `(() => {
      if (window.fitPanels) window.fitPanels();
      const sections = [...document.querySelectorAll(".snap-section")];
      const founderPhoto = document.querySelector(".contact-profile img");
      const sectionLabels = sections.map((section) => section.dataset.section || section.id || section.className);
      const navLabels = [...document.querySelectorAll("[data-nav] a")].map((link) => link.textContent.trim());
      const navTargets = [...document.querySelectorAll('a[href^="#"]')]
        .map((link) => link.getAttribute("href"))
        .filter((href) => href && href !== "#" && href !== "#top")
        .filter((href) => !document.querySelector(href));
      const overflowing = sections
        .map((section) => ({
          id: section.id || section.className,
          heightDelta: Math.abs(section.clientHeight - window.innerHeight),
          widthOverflow: section.scrollWidth - section.clientWidth,
          heightOverflow: section.scrollHeight - section.clientHeight,
        }))
        .filter((section) => section.heightDelta > 1 || section.widthOverflow > 3 || section.heightOverflow > 3);
      const founderFrame = founderPhoto?.closest(".contact-photo");
      const founderBox = founderFrame?.getBoundingClientRect();
      const founderImageBox = founderPhoto?.getBoundingClientRect();
      const founderStyle = founderPhoto ? getComputedStyle(founderPhoto) : null;
      const focalX = Number(founderPhoto?.dataset.focalX || 0.5);
      const focalY = Number(founderPhoto?.dataset.focalY || 0.5);
      let focalDelta = null;
      if (founderPhoto && founderBox?.width && founderBox?.height && founderImageBox?.width && founderImageBox?.height) {
        const offsetX = founderImageBox.left - founderBox.left;
        const offsetY = founderImageBox.top - founderBox.top;
        focalDelta = {
          x: Math.abs(offsetX + founderImageBox.width * focalX - founderBox.width / 2),
          y: Math.abs(offsetY + founderImageBox.height * focalY - founderBox.height / 2),
          croppedX: founderImageBox.width > founderBox.width + 1,
          croppedY: founderImageBox.height > founderBox.height + 1,
        };
      }
      return {
        sectionCount: sections.length,
        innerHeight: window.innerHeight,
        founderPhoto: founderPhoto
          ? {
              src: founderPhoto.getAttribute("src"),
              naturalWidth: founderPhoto.naturalWidth,
              naturalHeight: founderPhoto.naturalHeight,
              focalReady: founderPhoto.dataset.focalReady,
              focalX,
              focalY,
              objectPosition: founderStyle?.objectPosition || "",
              frameWidth: founderBox?.width || 0,
              frameHeight: founderBox?.height || 0,
              renderedWidth: founderImageBox?.width || 0,
              renderedHeight: founderImageBox?.height || 0,
              focalDelta,
            }
          : null,
        feedMode: document.documentElement.classList.contains("feed-mode"),
        activeIndex: window.KhaniFeed?.currentIndex?.() ?? -1,
        mainPosition: getComputedStyle(document.querySelector("main")).position,
        bodyOverflow: getComputedStyle(document.body).overflowY,
        scrollSnapType: getComputedStyle(document.documentElement).scrollSnapType,
        overscrollBehaviorY: getComputedStyle(document.documentElement).overscrollBehaviorY,
        introRunning: document.body.classList.contains("is-intro-running"),
        introLoaderDone: document.querySelector("[data-intro-loader]")?.classList.contains("is-done") ?? true,
        sectionLabels,
        navLabels,
        navTargets,
        overflowing,
      };
    })()`,
  );

  if (metrics.introRunning || !metrics.introLoaderDone) {
    throw new Error(`${viewport.name}: logo intro did not finish cleanly.`);
  }
  if (metrics.sectionCount < 3) throw new Error(`${viewport.name}: expected multiple snap panels.`);
  if (
    !metrics.founderPhoto ||
    !String(metrics.founderPhoto.src).includes("reza-khani-founder-original.jpg?v=20260519-founder-jpg-final2") ||
    metrics.founderPhoto.naturalWidth !== 2085 ||
    metrics.founderPhoto.naturalHeight !== 3783 ||
    metrics.founderPhoto.focalReady !== "true"
  ) {
    throw new Error(`${viewport.name}: corrected founder photo is not loaded ${JSON.stringify(metrics.founderPhoto)}.`);
  }
  if (
    (metrics.founderPhoto.focalDelta?.croppedX && metrics.founderPhoto.focalDelta.x > 2) ||
    (metrics.founderPhoto.focalDelta?.croppedY && metrics.founderPhoto.focalDelta.y > 2)
  ) {
    throw new Error(`${viewport.name}: founder photo focal point is not centered ${JSON.stringify(metrics.founderPhoto)}.`);
  }
  if (metrics.sectionLabels.join("|") !== metrics.navLabels.join("|")) {
    throw new Error(`${viewport.name}: nav labels do not match panels (${metrics.navLabels.join(", ")} vs ${metrics.sectionLabels.join(", ")}).`);
  }
  if (!metrics.feedMode) throw new Error(`${viewport.name}: transform feed mode is not active.`);
  if (metrics.activeIndex !== 0) throw new Error(`${viewport.name}: first panel is not active after load.`);
  if (metrics.mainPosition !== "fixed") throw new Error(`${viewport.name}: main panel stage is not fixed.`);
  if (metrics.bodyOverflow !== "hidden") throw new Error(`${viewport.name}: body scroll is not locked.`);
  if (String(metrics.scrollSnapType) !== "none") throw new Error(`${viewport.name}: native scroll snap is still active.`);
  if (metrics.overscrollBehaviorY !== "none") throw new Error(`${viewport.name}: page overscroll is not fully locked.`);
  if (metrics.navTargets.length) throw new Error(`${viewport.name}: broken nav targets ${metrics.navTargets.join(", ")}`);
  if (metrics.overflowing.length) {
    throw new Error(`${viewport.name}: panels do not fit viewport ${JSON.stringify(metrics.overflowing)}`);
  }

  if (viewport.mobile) {
    const menuState = await evaluate(
      client,
      `(() => {
        const toggle = document.querySelector("[data-nav-toggle]");
        const nav = document.querySelector("[data-nav]");
        const hero = document.querySelector(".hero");
        toggle?.click();
        const opened = nav?.classList.contains("is-open") && toggle?.getAttribute("aria-expanded") === "true";
        hero?.click();
        const closed = !nav?.classList.contains("is-open") && toggle?.getAttribute("aria-expanded") === "false";
        return { opened, closed };
      })()`,
    );

    if (!menuState.opened || !menuState.closed) {
      throw new Error(`${viewport.name}: mobile menu does not close after outside click.`);
    }
  }

  await evaluate(client, "window.KhaniFeed.goTo(0, { animate: false }); window.scrollTo(0, 0)");
  await wait(120);
  const wheelDeltas = viewport.mobile ? [220] : [36, 34, 28, 18, 12, -18, 10, 8];
  for (const deltaY of wheelDeltas) {
    await client.send("Input.dispatchMouseEvent", {
      type: "mouseWheel",
      x: Math.round(viewport.width / 2),
      y: Math.round(viewport.height / 2),
      deltaY,
      deltaX: 0,
    });
    await wait(55);
  }
  await wait(1400);

  const transition = await evaluate(
    client,
    `(() => {
      const sections = [...document.querySelectorAll(".snap-section")];
      return {
        activeIndex: window.KhaniFeed?.currentIndex?.() ?? -1,
        scrollY: window.scrollY,
        expectedIndex: 1,
        transitioning: document.documentElement.classList.contains("is-panel-transitioning"),
        viewportHeight: window.innerHeight,
      };
    })()`,
  );

  if (transition.activeIndex !== transition.expectedIndex || Math.abs(transition.scrollY) > 2 || transition.transitioning) {
    throw new Error(
      `${viewport.name}: wheel transition did not land cleanly on next panel ${JSON.stringify(transition)}.`,
    );
  }

  if (viewport.mobile) {
    await evaluate(
      client,
      `(() => {
        const sections = [...document.querySelectorAll(".snap-section")];
        window.KhaniFeed.goTo(sections.length - 1, { animate: false });
      })()`,
    );
    await wait(160);
    await client.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [{ x: Math.round(viewport.width * 0.35), y: Math.round(viewport.height * 0.62) }],
    });
    await wait(40);
    await client.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [{ x: Math.round(viewport.width * 0.35), y: Math.round(viewport.height * 0.86) }],
    });
    await wait(40);
    await client.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await wait(1450);

    const reverseTransition = await evaluate(
      client,
      `(() => {
        const sections = [...document.querySelectorAll(".snap-section")];
        return {
          activeIndex: window.KhaniFeed?.currentIndex?.() ?? -1,
          scrollY: window.scrollY,
          expectedIndex: sections.length - 2,
          transitioning: document.documentElement.classList.contains("is-panel-transitioning"),
        };
      })()`,
    );

    if (
      reverseTransition.activeIndex !== reverseTransition.expectedIndex ||
      Math.abs(reverseTransition.scrollY) > 2 ||
      reverseTransition.transitioning
    ) {
      throw new Error(
        `${viewport.name}: touch swipe from last panel did not return cleanly ${JSON.stringify(reverseTransition)}.`,
      );
    }
  }

  console.log(`${viewport.name}: ${metrics.sectionCount} panels fit ${viewport.width}x${viewport.height} and feed-scroll correctly.`);
}

async function stopChrome(chrome, userDataDir) {
  if (!chrome.killed) {
    chrome.kill("SIGTERM");
    await Promise.race([
      new Promise((resolve) => chrome.once("exit", resolve)),
      wait(1200),
    ]);
  }
  await rm(userDataDir, { recursive: true, force: true, maxRetries: 6, retryDelay: 150 });
}

async function main() {
  const userDataDir = await mkdtemp(join(tmpdir(), "khani-feed-check-"));
  const chrome = spawn(chromePath, [
    "--headless=new",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ]);

  chrome.stderr.on("data", () => {});

  try {
    const webSocketUrl = await waitForPageTarget();
    const client = await createClient(webSocketUrl);
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await client.send("Network.enable");
    await client.send("Network.setCacheDisabled", { cacheDisabled: true });

    await checkViewport(client, { name: "desktop", width: 1366, height: 768, mobile: false });
    await checkViewport(client, { name: "phone", width: 390, height: 844, mobile: true });

    client.close();
  } finally {
    await stopChrome(chrome, userDataDir);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
