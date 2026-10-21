const components = {
  browser: {
    category: "THE EXPERIENCE", title: "Browser dashboard", security: "OAuth 2.0 · PKCE sign-in",
    description: "Users upload recordings and search summaries and timestamped transcripts from the workspace. Cognito tokens stay in the current browser session.",
  },
  edge: {
    category: "EDGE & DELIVERY", title: "CloudFront + AWS WAF", security: "HTTPS · managed rules · IP rate limits",
    description: "CloudFront delivers the static application over HTTPS. AWS WAF adds managed common protections and request-rate limits at the edge.",
  },
  auth: {
    category: "IDENTITY", title: "Amazon Cognito", security: "OAuth authorization code · PKCE · optional MFA",
    description: "Cognito verifies workspace identities. API calls use short-lived access tokens; the public OAuth client has no embedded secret.",
  },
  api: {
    category: "AUTHENTICATED API", title: "Amazon API Gateway", security: "JWT authorizer · request throttling",
    description: "API Gateway validates the Cognito token before invoking Lambda. The API derives the owner from the verified token, never a browser-supplied ID.",
  },
  s3: {
    category: "PRIVATE OBJECT STORAGE", title: "Amazon S3", security: "Private · SSE-KMS · versioned · TLS-only",
    description: "Short-lived presigned POST policies upload recordings under account-scoped keys. S3 blocks public access, enforces TLS, and encrypts stored data.",
  },
  starter: {
    category: "EVENT PROCESSING", title: "Starter Lambda", security: "Owner validation · least-privilege IAM",
    description: "An S3 event is checked against its meeting record and owner before a transcription job starts. Processing capacity is bounded.",
  },
  transcribe: {
    category: "SPEECH RECOGNITION", title: "Amazon Transcribe", security: "Timestamped transcript · speaker labels",
    description: "Transcribe converts the recording to timestamped text and speaker-labelled segments, then reports job completion through EventBridge.",
  },
  processor: {
    category: "SUMMARIZATION & INDEXING", title: "Processor Lambda", security: "Scoped roles · bounded retries · concurrency cap",
    description: "The processor requests a grounded analysis, saves the complete transcript, indexes searchable text, updates meeting status, and publishes a ready notification.",
  },
  bedrock: {
    category: "GENERATIVE ANALYSIS", title: "Amazon Bedrock", security: "Model-level InvokeModel permission",
    description: "Bedrock extracts a concise summary, key decisions, actions, and topics from the transcript as structured data.",
  },
  dynamodb: {
    category: "MEETING RECORDS & SEARCH", title: "Amazon DynamoDB", security: "Encrypted at rest · owner-filtered results",
    description: "Meeting summaries and transcript-search chunks are stored with the authenticated owner ID, keeping search and detail results account-scoped.",
  },
  sns: {
    category: "MEETING-READY NOTIFICATION", title: "Amazon SNS", security: "Encrypted topic · confirmed subscriptions",
    description: "SNS sends an optional notification when analysis is ready. Email subscriptions receive messages after the recipient confirms.",
  },
};

const componentOrder = Object.keys(components);
const canvas = document.querySelector("#canvas-wrap");
const art = document.querySelector("#architecture-art");
const flowButton = document.querySelector("#flow-toggle");
const buttons = document.querySelector("#service-buttons");
const camera = { turn: -2, tilt: 1, zoom: 1 };
const bounds = { zoomMin: 0.78, zoomMax: 1.3, tiltMin: -12, tiltMax: 20 };
let drag = null;
let selected = "browser";
let playing = false;
let svgDocument;

function renderCamera() {
  art.style.setProperty("--turn", `${camera.turn}deg`);
  art.style.setProperty("--tilt", `${camera.tilt}deg`);
  art.style.setProperty("--zoom", String(camera.zoom));
}

function selectComponent(id) {
  const item = components[id];
  if (!item) return;
  selected = id;
  document.querySelectorAll(".service-button").forEach((button) => {
    const active = button.dataset.component === id;
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  document.querySelector("#detail-category").textContent =
    `${item.category} · ${String(componentOrder.indexOf(id) + 1).padStart(2, "0")} / 11`;
  document.querySelector("#detail-title").textContent = item.title;
  document.querySelector("#detail-description").textContent = item.description;
  document.querySelector("#detail-security-value").textContent = item.security;
  document.querySelector("#detail-icon").textContent = String(componentOrder.indexOf(id) + 1).padStart(2, "0");
  if (svgDocument) {
    svgDocument.querySelectorAll("[data-component]").forEach((node) => {
      node.classList.toggle("is-selected", node.dataset.component === id);
      node.setAttribute("aria-pressed", String(node.dataset.component === id));
    });
  }
}

function setFlow(next) {
  playing = next;
  canvas.classList.toggle("is-playing", playing);
  flowButton.setAttribute("aria-pressed", String(playing));
  flowButton.innerHTML = playing
    ? '<span aria-hidden="true">Ⅱ</span><span>Pause data flow</span>'
    : '<span aria-hidden="true">▶</span><span>Play data flow</span>';
  if (svgDocument) svgDocument.documentElement.classList.toggle("flow-active", playing);
}

function prepareDiagram() {
  svgDocument = art.contentDocument;
  if (!svgDocument) return;
  const style = svgDocument.createElementNS("http://www.w3.org/2000/svg", "style");
  style.textContent = `
    [data-component] { cursor: pointer; transform-box: fill-box; transform-origin: center; transition: filter .2s, opacity .2s; }
    [data-component]:hover, [data-component].is-selected { filter: drop-shadow(0 0 13px rgba(117,232,190,.8)); }
    [data-component].is-selected { opacity: 1; }
    .flow-path { transition: opacity .2s; }
    .flow-active .flow-path { animation: data-pulse 1.1s linear infinite; }
    .flow-active .flow-path:nth-child(2n) { animation-delay: .24s; }
    @keyframes data-pulse { to { stroke-dashoffset: -32; } }
    @media (prefers-reduced-motion: reduce) { .flow-active .flow-path { animation: none; } }
  `;
  svgDocument.documentElement.append(style);
  svgDocument.querySelectorAll("[data-component]").forEach((node) => {
    node.addEventListener("click", () => selectComponent(node.dataset.component));
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectComponent(node.dataset.component);
      }
    });
  });
  setFlow(playing);
  selectComponent(selected);
}

componentOrder.forEach((id, index) => {
  const button = document.createElement("button");
  button.className = "service-button";
  button.type = "button";
  button.dataset.component = id;
  button.setAttribute("aria-pressed", "false");
  button.innerHTML = `<span class="service-number">${String(index + 1).padStart(2, "0")}</span><span class="service-name">${components[id].title}</span>`;
  button.addEventListener("click", () => selectComponent(id));
  buttons.append(button);
});

art.addEventListener("load", prepareDiagram);
flowButton.addEventListener("click", () => setFlow(!playing));
document.querySelector("#rotate-left").addEventListener("click", () => { camera.turn -= 7; renderCamera(); });
document.querySelector("#rotate-right").addEventListener("click", () => { camera.turn += 7; renderCamera(); });
document.querySelector("#zoom-in").addEventListener("click", () => { camera.zoom = Math.min(bounds.zoomMax, camera.zoom + .08); renderCamera(); });
document.querySelector("#zoom-out").addEventListener("click", () => { camera.zoom = Math.max(bounds.zoomMin, camera.zoom - .08); renderCamera(); });
document.querySelector("#reset-camera").addEventListener("click", () => {
  camera.turn = -2;
  camera.tilt = 1;
  camera.zoom = 1;
  renderCamera();
});

canvas.addEventListener("wheel", (event) => {
  if (event.ctrlKey || event.metaKey) return;
  event.preventDefault();
  camera.zoom = Math.max(bounds.zoomMin, Math.min(bounds.zoomMax, camera.zoom + (event.deltaY < 0 ? .04 : -.04)));
  renderCamera();
}, { passive: false });

canvas.addEventListener("pointerdown", (event) => {
  if (event.target.closest("button")) return;
  drag = { x: event.clientX, y: event.clientY, turn: camera.turn, tilt: camera.tilt };
  canvas.setPointerCapture(event.pointerId);
  canvas.classList.add("is-dragging");
});
canvas.addEventListener("pointermove", (event) => {
  if (!drag) return;
  camera.turn = drag.turn + (event.clientX - drag.x) * .16;
  camera.tilt = Math.max(bounds.tiltMin, Math.min(bounds.tiltMax, drag.tilt - (event.clientY - drag.y) * .12));
  renderCamera();
});
function finishDrag() {
  drag = null;
  canvas.classList.remove("is-dragging");
}
canvas.addEventListener("pointerup", finishDrag);
canvas.addEventListener("pointercancel", finishDrag);
canvas.addEventListener("keydown", (event) => {
  const step = event.shiftKey ? 12 : 5;
  if (event.key === "ArrowLeft") camera.turn -= step;
  else if (event.key === "ArrowRight") camera.turn += step;
  else if (event.key === "ArrowUp") camera.tilt = Math.min(bounds.tiltMax, camera.tilt + step);
  else if (event.key === "ArrowDown") camera.tilt = Math.max(bounds.tiltMin, camera.tilt - step);
  else if (event.key === "+" || event.key === "=") camera.zoom = Math.min(bounds.zoomMax, camera.zoom + .06);
  else if (event.key === "-") camera.zoom = Math.max(bounds.zoomMin, camera.zoom - .06);
  else if (event.key === "Home") {
    camera.turn = -2;
    camera.tilt = 1;
    camera.zoom = 1;
  } else return;
  event.preventDefault();
  renderCamera();
});

renderCamera();
selectComponent(selected);
