const components = {
  browser: {
    category: "THE EXPERIENCE", title: "Browser dashboard", icon: "▧", step: "01 / 11",
    security: "OAuth 2.0 · PKCE sign-in",
    description: "The team uploads recordings and searches summaries and timestamped transcripts. The dashboard keeps OAuth tokens in the current browser tab and sends the short-lived access token only to the API.",
  },
  edge: {
    category: "EDGE & DELIVERY", title: "CloudFront + AWS WAF", icon: "◇", step: "02 / 11",
    security: "HTTPS · managed rules · rate limits",
    description: "CloudFront serves static dashboard assets over HTTPS from a private S3 origin. AWS WAF adds managed common protections and per-IP request limits at the edge.",
  },
  auth: {
    category: "IDENTITY", title: "Amazon Cognito", icon: "◎", step: "03 / 11",
    security: "Password policy · optional authenticator MFA",
    description: "Cognito provides verified account sign-in using OAuth authorization code with PKCE. The public client has no embedded secret; optional authenticator-app MFA can be enabled for each account.",
  },
  api: {
    category: "AUTHENTICATED API", title: "Amazon API Gateway", icon: "⌘", step: "04 / 11",
    security: "JWT authorizer · request throttling",
    description: "The HTTP API validates Cognito JWTs before invoking the backend and applies burst and steady-state throttling. Its Lambda integration accepts only the verified user's identity claim.",
  },
  s3: {
    category: "PRIVATE OBJECT STORAGE", title: "Amazon S3", icon: "▤", step: "05 / 11",
    security: "Private access · SSE-KMS · versioning · TLS-only",
    description: "Recordings arrive by short-lived presigned upload URLs under an account-specific key. The bucket blocks public access, enforces TLS, encrypts objects with a rotating KMS key, and keeps versions for recovery.",
  },
  starter: {
    category: "EVENT PROCESSING", title: "S3-triggered Lambda", icon: "λ", step: "06 / 11",
    security: "Least-privilege role · bounded concurrency",
    description: "An upload event is checked against its meeting record and owner before the function starts a transcription job. Its IAM role can access only the required upload, transcript, and service resources.",
  },
  transcribe: {
    category: "SPEECH RECOGNITION", title: "Amazon Transcribe", icon: "≋", step: "07 / 11",
    security: "Speaker labels · encrypted S3 output",
    description: "Transcribe converts audio to timestamped words and speaker-labelled segments. EventBridge forwards job completion or failure to the processor without polling.",
  },
  processor: {
    category: "SUMMARIZATION & INDEXING", title: "Processor Lambda", icon: "λ", step: "08 / 11",
    security: "Scoped IAM · retry policy · concurrency cap",
    description: "The processor verifies the meeting owner, loads the transcript, requests a grounded summary from Bedrock, writes the transcript to S3, indexes searchable chunks, and publishes a ready notification.",
  },
  bedrock: {
    category: "GENERATIVE ANALYSIS", title: "Amazon Bedrock", icon: "✳", step: "09 / 11",
    security: "Model-level InvokeModel permission",
    description: "Bedrock receives the transcript and returns a constrained JSON result with a concise summary, key decisions, action items, topics, and participants. The prompt instructs it not to invent owners or deadlines.",
  },
  dynamodb: {
    category: "MEETING RECORDS & SEARCH", title: "Amazon DynamoDB", icon: "▤", step: "10 / 11",
    security: "At-rest encryption · owner-filtered access",
    description: "DynamoDB stores meeting metadata, summaries, and transcript search chunks. Each item carries its Cognito owner ID, and the API filters search and detail results to that authenticated account.",
  },
  sns: {
    category: "MEETING-READY NOTIFICATION", title: "Amazon SNS", icon: "✉", step: "11 / 11",
    security: "Encrypted topic · confirmed subscription",
    description: "When processing completes, the Lambda publishes a ready event to an encrypted SNS topic. An optional email subscription is activated only after the recipient confirms it.",
  },
};

const stage = document.querySelector("#diagram-stage");
const diagram = document.querySelector("#diagram-svg");
const nodes = [...document.querySelectorAll(".service-node")];
const flowButton = document.querySelector("#flow-toggle");
const defaults = { zoom: 1, turn: 0, panX: 0, panY: 0 };
const camera = { ...defaults };
let drag = null;

function selectComponent(id) {
  const item = components[id];
  if (!item) return;
  nodes.forEach((node) => {
    const active = node.dataset.component === id;
    node.classList.toggle("is-selected", active);
    node.setAttribute("aria-pressed", String(active));
  });
  document.querySelector("#detail-category").textContent = item.category;
  document.querySelector("#detail-title").textContent = item.title;
  document.querySelector("#detail-icon").textContent = item.icon;
  document.querySelector("#detail-description").textContent = item.description;
  document.querySelector("#detail-step").textContent = item.step;
  document.querySelector("#detail-security").textContent = item.security;
}

function renderCamera() {
  diagram.style.setProperty("--zoom", String(camera.zoom));
  diagram.style.setProperty("--turn", `${camera.turn}deg`);
  diagram.style.setProperty("--pan-x", `${camera.panX}px`);
  diagram.style.setProperty("--pan-y", `${camera.panY}px`);
}

function stopFlow() {
  stage.classList.remove("is-playing");
  flowButton.setAttribute("aria-pressed", "false");
  flowButton.innerHTML = '<span class="play-icon" aria-hidden="true">▶</span><span>Play data flow</span>';
}

nodes.forEach((node) => {
  node.addEventListener("click", () => selectComponent(node.dataset.component));
  node.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectComponent(node.dataset.component);
    }
  });
});

flowButton.addEventListener("click", () => {
  const playing = !stage.classList.contains("is-playing");
  stage.classList.toggle("is-playing", playing);
  flowButton.setAttribute("aria-pressed", String(playing));
  flowButton.innerHTML = playing
    ? '<span class="play-icon" aria-hidden="true">Ⅱ</span><span>Pause data flow</span>'
    : '<span class="play-icon" aria-hidden="true">▶</span><span>Play data flow</span>';
});

document.querySelector("#rotate-left").addEventListener("click", () => {
  camera.turn -= 7;
  renderCamera();
});
document.querySelector("#rotate-right").addEventListener("click", () => {
  camera.turn += 7;
  renderCamera();
});
document.querySelector("#zoom-in").addEventListener("click", () => {
  camera.zoom = Math.min(1.3, camera.zoom + 0.08);
  renderCamera();
});
document.querySelector("#zoom-out").addEventListener("click", () => {
  camera.zoom = Math.max(0.78, camera.zoom - 0.08);
  renderCamera();
});
document.querySelector("#reset-camera").addEventListener("click", () => {
  Object.assign(camera, defaults);
  renderCamera();
});

stage.addEventListener("wheel", (event) => {
  if (event.ctrlKey || event.metaKey) return;
  event.preventDefault();
  camera.zoom = Math.max(0.78, Math.min(1.3, camera.zoom + (event.deltaY < 0 ? 0.04 : -0.04)));
  renderCamera();
}, { passive: false });

stage.addEventListener("pointerdown", (event) => {
  if (event.target.closest(".service-node") || event.target.closest("button")) return;
  drag = { x: event.clientX, y: event.clientY, turn: camera.turn, panY: camera.panY };
  stage.setPointerCapture(event.pointerId);
  diagram.classList.add("is-dragging");
});
stage.addEventListener("pointermove", (event) => {
  if (!drag) return;
  camera.turn = drag.turn + (event.clientX - drag.x) * 0.16;
  camera.panY = drag.panY + (event.clientY - drag.y) * 0.18;
  renderCamera();
});
function finishDrag() {
  drag = null;
  diagram.classList.remove("is-dragging");
}
stage.addEventListener("pointerup", finishDrag);
stage.addEventListener("pointercancel", finishDrag);

selectComponent("browser");
