import * as ort from './runtime/ort.wasm.min.mjs';
import {sanitizePose, buildInputs, recoverFields} from './geometry.mjs';

// Runtime stays in this module worker: no main-thread ORT, proxy or thread pool.
ort.env.wasm.numThreads = 1;
ort.env.wasm.proxy = false;
ort.env.wasm.wasmPaths = new URL('./runtime/', import.meta.url).href;

let sessionPromise = null, sessionHash = null;

async function getSession(config) {
  const hash = config.onnxSha256;
  if (typeof hash !== 'string' || !/^[a-f\d]{64}$/i.test(hash)) throw new Error('Missing model integrity hash');
  if (sessionPromise && hash !== sessionHash) throw new Error('Model configuration changed; reload the explorer');
  if (!sessionPromise) {
    sessionHash = hash;
    sessionPromise = (async () => {
      const response = await fetch(new URL('./model/geometry-unet.onnx', import.meta.url));
      if (!response.ok) throw new Error(`Model download failed (${response.status})`);
      const bytes = await response.arrayBuffer();
      if (!globalThis.crypto?.subtle) throw new Error('Model integrity verification requires HTTPS or localhost');
      const digest = await crypto.subtle.digest('SHA-256', bytes);
      const actual = Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, '0')).join('');
      if (actual !== hash.toLowerCase()) throw new Error('Model integrity check failed');
      const session = await ort.InferenceSession.create(bytes, {
        executionProviders: ['wasm'], graphOptimizationLevel: 'all'
      });
      if (!session.inputNames.includes('geometry') || !session.outputNames.includes('response')) {
        await session.release();
        throw new Error('Unexpected model input/output names');
      }
      return session;
    })().catch(error => { sessionPromise = null; sessionHash = null; throw error; });
  }
  return sessionPromise;
}

async function predict(message) {
  const {id, config} = message || {};
  try {
    const started = performance.now();
    if (config?.nx !== 256 || config?.ny !== 128) throw new Error('The saved model requires a 256 × 128 grid');
    const pose = sanitizePose(config, message.pose);
    const {data, mask} = buildInputs(config, pose);
    const session = await getSession(config);
    const tensor = new ort.Tensor('float32', data, [1, 4, config.ny, config.nx]);
    let output;
    try {
      output = await session.run({geometry: tensor});
      const response = output.response;
      if (!response || response.type !== 'float32' || response.dims.length !== 4 ||
          response.dims.some((value, index) => value !== [1, 3, config.ny, config.nx][index])) {
        throw new Error('Unexpected model output shape');
      }
      const {u, v, cp} = recoverFields(config, response.data, mask);
      self.postMessage({id, pose, u, v, cp, mask, elapsedMs: performance.now() - started},
        [u.buffer, v.buffer, cp.buffer, mask.buffer]);
    } finally {
      tensor.dispose();
      if (output) for (const tensor of Object.values(output)) tensor.dispose();
    }
  } catch (error) {
    self.postMessage({id, error: error instanceof Error ? error.message : String(error)});
  }
}

// InferenceSession.run is serialized. The UI keeps one in-flight request and
// replaces its pending pose with the newest interaction to avoid a stale queue.
let queue = Promise.resolve();
self.addEventListener('message', event => { queue = queue.then(() => predict(event.data)); });
