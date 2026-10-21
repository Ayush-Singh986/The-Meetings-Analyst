const icons = {
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="7" height="7" rx="1.3"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.3"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.3"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.3"/></svg>',
  calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5.5" width="17" height="15" rx="2"/><path d="M7.5 3.5v4M16.5 3.5v4M3.5 10h17M8 14h.01M12 14h.01M16 14h.01M8 17h.01M12 17h.01"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.2 4L19 7"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 4.4 4.4"/></svg>',
  sparkle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="m19 16 .9 2.1L22 19l-2.1.9L19 22l-.9-2.1L16 19l2.1-.9L19 16Z"/></svg>',
  settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1a1.7 1.7 0 0 1-2.4 2.4l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.3a1.7 1.7 0 0 1-3.4 0v-.2a1.7 1.7 0 0 0-2.9-1.2l-.1.1a1.7 1.7 0 0 1-2.4-2.4l.1-.1a1.7 1.7 0 0 0-1.2-2.9h-.3a1.7 1.7 0 0 1 0-3.4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a1.7 1.7 0 0 1 2.4-2.4l.1.1a1.7 1.7 0 0 0 2.9-1.2v-.3a1.7 1.7 0 0 1 3.4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a1.7 1.7 0 0 1 2.4 2.4l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.3a1.7 1.7 0 0 1 0 3.4h-.2a1.7 1.7 0 0 0-1.2 2.9Z"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  flag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V5m0 0c6-4 8 4 14 0v10c-6 4-8-4-14 0"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/></svg>',
  "arrow-up-right": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M8 7h9v9"/></svg>',
  filter: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M7 12h10m-7 6h4"/></svg>',
  sort: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8 5v14m0 0-4-4m4 4 4-4M16 19V5m0 0-4 4m4-4 4 4"/></svg>',
  refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9a7 7 0 0 1 11.7-2L20 12M4 12l2.8 5a7 7 0 0 0 11.7-2"/></svg>',
  diagram: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m4.5 7.8 7.5 4.4 7.5-4.4M12 12.2V21"/></svg>',
  audio: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10v4m4-8v12m4-15v18m4-13v8m4-11v14"/></svg>',
};

const sampleMeetings = [
  {
    meetingId: "sample-1", title: "Product launch — weekly sync", fileName: "product-launch-sync.mp4",
    status: "READY", createdAt: "2026-10-21T10:30:00+05:30", duration: "42 min",
    participants: ["AM", "JL", "SK", "DP"], summary: "The launch remains on track for November 12. The team agreed to freeze the feature set by Friday and give customer support the updated FAQ before the beta opens.",
    keyDecisions: ["Keep the November 12 launch date; the release candidate will be ready for review on November 5.", "Move the analytics dashboard to phase two so the team can protect the launch scope."],
    actionItems: [{ owner: "Jamie Lee", task: "Share the updated customer FAQ with support.", due_date: "October 23" }, { owner: "Sam Kim", task: "Send the release-candidate checklist to engineering.", due_date: "October 24" }],
    topics: ["Launch planning", "Scope", "Customer support"],
    transcript: "Speaker 1 · [00:00:04] Thanks, everyone. Let's start with the launch timeline.\nSpeaker 2 · [00:02:18] We can keep November 12 if we freeze the feature set by Friday.\nSpeaker 3 · [00:06:42] Agreed. The analytics dashboard can move to phase two.\nSpeaker 1 · [00:14:09] Jamie, can you share the customer FAQ with support by Thursday?\nSpeaker 2 · [00:14:15] Yes, I'll have it over by October 23.\nSpeaker 4 · [00:28:33] The release candidate should be ready for review on November 5.",
  },
  {
    meetingId: "sample-2", title: "Q4 budget & resourcing", fileName: "q4-budget-review.wav",
    status: "READY", createdAt: "2026-10-20T15:00:00+05:30", duration: "36 min",
    participants: ["AM", "TR", "JL"], summary: "Finance approved the revised Q4 budget, including two engineering contractor roles. Taylor will share the final headcount plan with the leadership team by October 24.",
    keyDecisions: ["Approve the revised Q4 budget and two engineering contractor roles.", "Review contractor spend again after the first six weeks."],
    actionItems: [{ owner: "Taylor Reed", task: "Share the approved headcount plan with leadership.", due_date: "October 24" }, { owner: "Alex Morgan", task: "Schedule a six-week contractor spend review.", due_date: "December 5" }],
    topics: ["Budget approval", "Hiring", "Q4 planning"],
    transcript: "Speaker 1 · [00:00:10] The revised Q4 budget is ready for a decision.\nSpeaker 2 · [00:04:31] Finance approves the two engineering contractor roles.\nSpeaker 3 · [00:11:02] Let's review contractor spend again after six weeks.\nSpeaker 2 · [00:18:46] I'll share the final headcount plan with leadership by October 24.",
  },
  {
    meetingId: "sample-3", title: "Design critique — onboarding", fileName: "onboarding-design-critique.mp3",
    status: "READY", createdAt: "2026-10-20T11:00:00+05:30", duration: "51 min",
    participants: ["JL", "SK", "DP", "AM"], summary: "The team chose a shorter onboarding flow with a skippable profile step. Design will test the revised welcome screen with five customers before handing off final mockups.",
    keyDecisions: ["Make the profile step optional and keep onboarding to three screens.", "Validate the revised welcome screen with five customers."],
    actionItems: [{ owner: "Dev Patel", task: "Recruit five customers for the onboarding test.", due_date: "October 27" }],
    topics: ["Onboarding", "User research", "Design"],
    transcript: "Speaker 1 · [00:01:26] The profile step is adding friction before people see the product.\nSpeaker 2 · [00:08:14] What if we make it optional and keep the flow to three screens?\nSpeaker 3 · [00:16:03] I can recruit five customers for a quick test by next Tuesday.",
  },
  {
    meetingId: "sample-4", title: "Customer feedback roundup", fileName: "customer-feedback-october.mp4",
    status: "READY", createdAt: "2026-10-19T16:30:00+05:30", duration: "29 min",
    participants: ["DP", "AM", "TR"], summary: "Customers are asking for simpler exports and clearer status updates. The team will prioritize CSV exports and review support ticket volume at the end of the month.",
    keyDecisions: ["Prioritize CSV exports for the next release.", "Review support volume before committing to a notification redesign."],
    actionItems: [{ owner: "Taylor Reed", task: "Bring support ticket trends to the next product review.", due_date: "October 30" }],
    topics: ["Customer feedback", "Exports", "Support"],
    transcript: "Speaker 1 · [00:03:10] Three customers asked whether they can export their reports as a CSV.\nSpeaker 2 · [00:09:47] That's the clearest signal; let's prioritize CSV for the next release.\nSpeaker 3 · [00:22:11] I'll bring support ticket trends to the product review on October 30.",
  },
  {
    meetingId: "sample-5", title: "Engineering stand-up", fileName: "engineering-standup.mp4",
    status: "PROCESSING", createdAt: "2026-10-19T10:15:00+05:30", duration: "18 min",
    participants: ["SK", "DP", "JL"], summary: "", keyDecisions: [], actionItems: [], topics: [],
  },
  {
    meetingId: "sample-6", title: "Marketing × Product planning", fileName: "marketing-product-planning.mp3",
    status: "READY", createdAt: "2026-10-16T14:00:00+05:30", duration: "44 min",
    participants: ["AM", "TR", "JL"], summary: "Marketing and product aligned on the beta announcement and a coordinated customer email. Draft copy will be reviewed before the end of the month.",
    keyDecisions: ["Send the beta announcement alongside the customer email.", "Use the new product positioning in both launch channels."],
    actionItems: [{ owner: "Jamie Lee", task: "Share the launch email draft for review.", due_date: "October 28" }],
    topics: ["Beta launch", "Marketing", "Customer communications"],
    transcript: "Speaker 1 · [00:04:02] We'll coordinate the beta announcement with the customer email.\nSpeaker 2 · [00:10:17] Let's use the updated product positioning in both places.\nSpeaker 3 · [00:24:31] I'll share the draft before the end of the month.",
  },
  {
    meetingId: "sample-7", title: "One-on-one — Jamie & Alex", fileName: "jamie-alex-one-on-one.m4a",
    status: "READY", createdAt: "2026-10-16T09:30:00+05:30", duration: "31 min",
    participants: ["JL", "AM"], summary: "Jamie is interested in leading the research work for next quarter. Alex will review the project brief together with Jamie during their next one-on-one.",
    keyDecisions: ["Jamie will draft a short research brief for the next-quarter planning session."],
    actionItems: [{ owner: "Jamie Lee", task: "Draft a research brief for next-quarter planning.", due_date: "November 3" }],
    topics: ["Career growth", "Research", "Planning"],
    transcript: "Speaker 1 · [00:06:14] I'd love to take the lead on research next quarter.\nSpeaker 2 · [00:10:33] Put together a short brief and we'll review it in our next one-on-one.",
  },
  {
    meetingId: "sample-8", title: "Weekly team check-in", fileName: "weekly-team-checkin.mp4",
    status: "READY", createdAt: "2026-10-15T11:00:00+05:30", duration: "26 min",
    participants: ["AM", "SK", "DP", "TR"], summary: "The team resolved the staging environment issue and agreed to share blockers earlier in the week. The new weekly release note template will be used from Monday.",
    keyDecisions: ["Adopt the weekly release note template starting Monday.", "Raise cross-team blockers by Tuesday rather than waiting for the weekly check-in."],
    actionItems: [{ owner: "Sam Kim", task: "Publish the weekly release note template.", due_date: "October 19" }],
    topics: ["Team process", "Release notes", "Blockers"],
    transcript: "Speaker 1 · [00:02:19] The staging environment is back up now.\nSpeaker 2 · [00:08:25] Let's start using the new release-note template on Monday.\nSpeaker 3 · [00:15:40] If a blocker crosses teams, let's raise it by Tuesday.",
  },
];

const state = {
  apiUrl: sessionStorage.getItem("briefly-api-url") || "",
  token: sessionStorage.getItem("briefly-api-token") || "",
  connected: false,
  view: "overview",
  filter: "all",
  sort: "newest",
  chartDays: 7,
  chartRangeFilter: null,
  query: "",
  meetings: sampleMeetings,
  visibleCount: 5,
  searchRequest: 0,
  searchTimer: null,
  apiUrl: window.BRIEFLY_CONFIG?.apiUrl || "",
  accessToken: sessionStorage.getItem("briefly-access-token") || "",
  refreshToken: sessionStorage.getItem("briefly-refresh-token") || "",
  tokenExpiresAt: Number(sessionStorage.getItem("briefly-token-expires-at") || 0),
};

const elements = {
  list: document.querySelector("#meeting-list"),
  empty: document.querySelector("#empty-state"),
  count: document.querySelector("#list-count"),
  loadMore: document.querySelector("#load-more"),
  search: document.querySelector("#meeting-search"),
  input: document.querySelector("#file-input"),
  settingsModal: document.querySelector("#settings-modal"),
  detailModal: document.querySelector("#detail-modal"),
  toastRegion: document.querySelector("#toast-region"),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " error" : ""}`;
  toast.textContent = message;
  elements.toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

function openModal(modal) {
  modal.hidden = false;
  document.body.style.overflow = "hidden";
  const firstInput = modal.querySelector("input");
  if (firstInput) window.setTimeout(() => firstInput.focus(), 30);
}

function closeModal(modal) {
  modal.hidden = true;
  if (elements.settingsModal.hidden && elements.detailModal.hidden) {
    document.body.style.overflow = "";
  }
}

function setConnection(connected) {
  state.connected = connected;
  const pill = document.querySelector("#connection-status");
  pill.classList.toggle("is-connected", connected);
  pill.lastElementChild.textContent = connected ? "Private workspace" : "Sample workspace";
  document.querySelector("#signout-button").hidden = !connected;
}

function authConfig() {
  return window.BRIEFLY_CONFIG || {};
}

function randomToken(length = 64) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

function base64Url(bytes) {
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeJwt(token) {
  try {
    const encoded = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(Array.from(atob(encoded), (character) => (
      `%${character.charCodeAt(0).toString(16).padStart(2, "0")}`
    )).join("")));
  } catch {
    return {};
  }
}

function clearSession() {
  ["briefly-access-token", "briefly-refresh-token", "briefly-token-expires-at", "briefly-oauth-state", "briefly-oauth-verifier"]
    .forEach((key) => sessionStorage.removeItem(key));
  state.accessToken = "";
  state.refreshToken = "";
  state.tokenExpiresAt = 0;
  state.meetings = sampleMeetings;
  state.query = "";
  elements.search.value = "";
  setConnection(false);
}

async function exchangeCodeForSession(code, verifier) {
  const config = authConfig();
  const response = await fetch(`https://${config.userPoolDomain}.auth.${config.region}.amazoncognito.com/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: config.userPoolClientId,
      code,
      redirect_uri: config.dashboardUrl,
      code_verifier: verifier,
    }),
  });
  const result = await response.json();
  if (!response.ok || !result.access_token || !result.refresh_token) {
    throw new Error(result.error_description || result.error || "Secure sign-in could not be completed.");
  }
  state.accessToken = result.access_token;
  state.refreshToken = result.refresh_token;
  state.tokenExpiresAt = Date.now() + result.expires_in * 1000;
  sessionStorage.setItem("briefly-access-token", state.accessToken);
  sessionStorage.setItem("briefly-refresh-token", state.refreshToken);
  sessionStorage.setItem("briefly-token-expires-at", String(state.tokenExpiresAt));
  sessionStorage.removeItem("briefly-oauth-state");
  sessionStorage.removeItem("briefly-oauth-verifier");
  window.history.replaceState(null, "", window.location.pathname);
  return result.id_token || "";
}

async function refreshSession() {
  if (!state.refreshToken) {
    clearSession();
    return false;
  }
  const config = authConfig();
  const response = await fetch(`https://${config.userPoolDomain}.auth.${config.region}.amazoncognito.com/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: config.userPoolClientId,
      refresh_token: state.refreshToken,
    }),
  });
  if (!response.ok) {
    clearSession();
    return false;
  }
  const result = await response.json();
  state.accessToken = result.access_token;
  state.tokenExpiresAt = Date.now() + (result.expires_in || 3600) * 1000;
  sessionStorage.setItem("briefly-access-token", state.accessToken);
  sessionStorage.setItem("briefly-token-expires-at", String(state.tokenExpiresAt));
  return true;
}

async function apiRequest(path, options = {}, retry = true) {
  if (!state.accessToken || !state.refreshToken) {
    throw new Error("Sign in to your private workspace to continue.");
  }
  if (state.tokenExpiresAt && Date.now() >= state.tokenExpiresAt - 60000) {
    const refreshed = await refreshSession();
    if (!refreshed) throw new Error("Your session expired. Sign in again to continue.");
  }
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${state.accessToken}`);
  if (options.body && !headers.has("content-type")) {
    headers.set("Content-Type", "application/json");
  }
  const result = await fetch(`${state.apiUrl}${path}`, { ...options, headers });
  if (result.status === 401 && retry && await refreshSession()) {
    return apiRequest(path, options, false);
  }
  if (!result.ok) {
    let message = `The workspace returned an error (${result.status}).`;
    try {
      const payload = await result.json();
      if (payload.error) message = payload.error;
    } catch {
      // The response may not include JSON for gateway or network errors.
    }
    throw new Error(message);
  }
  return result.json();
}

function toDateLabel(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (isToday) return `Today · ${date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
  if (date.toDateString() === yesterday.toDateString()) return `Yesterday · ${date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function initialsFor(value) {
  const parts = String(value || "").trim().split(/\s+/);
  return parts.length > 1 ? `${parts[0][0]}${parts[1][0]}`.toUpperCase() : (parts[0] || "?").slice(0, 2).toUpperCase();
}

function sampleSearchText(meeting) {
  return [
    meeting.title, meeting.fileName, meeting.summary, ...(meeting.keyDecisions || []),
    ...(meeting.topics || []), ...(meeting.transcript ? [meeting.transcript] : []),
    ...(meeting.actionItems || []).flatMap((item) => [item.owner, item.task, item.due_date]),
  ].join(" ").toLowerCase();
}

function filteredMeetings() {
  let meetings = state.meetings;
  if (state.view === "decisions") {
    meetings = meetings.filter((meeting) => (meeting.actionItems || []).length > 0);
  }
  if (state.filter !== "all") {
    meetings = meetings.filter((meeting) => state.filter === "PROCESSING"
      ? meeting.status === "PROCESSING" || meeting.status === "UPLOADING"
      : meeting.status === state.filter);
  }
  if (state.query && !state.connected) {
    const phrase = state.query.toLowerCase();
    meetings = meetings.filter((meeting) => sampleSearchText(meeting).includes(phrase));
  }
  if (state.chartRangeFilter) {
    meetings = meetings.filter((meeting) => {
      const time = new Date(meeting.createdAt).getTime();
      return Number.isFinite(time)
        && time >= state.chartRangeFilter.start
        && time < state.chartRangeFilter.end;
    });
  }
  meetings = [...meetings].sort((left, right) => {
    const difference = new Date(left.createdAt).getTime() - new Date(right.createdAt).getTime();
    return state.sort === "newest" ? -difference : difference;
  });
  return meetings;
}

function meetingStatus(status) {
  const normal = String(status || "").toUpperCase();
  if (normal === "READY") return { label: "Ready", css: "" };
  if (normal === "FAILED") return { label: "Needs attention", css: "failed" };
  return { label: "Processing", css: "processing" };
}

function renderMeeting(meeting) {
  const people = Array.isArray(meeting.participants) ? meeting.participants : [];
  const avatars = people.slice(0, 3).map((person) => (
    `<span class="participant-avatar">${escapeHtml(initialsFor(person))}</span>`
  )).join("");
  const morePeople = people.length > 3 ? `<span class="participant-more">+${people.length - 3}</span>` : "";
  const status = meetingStatus(meeting.status);
  const duration = meeting.duration ? ` · ${escapeHtml(meeting.duration)}` : "";
  const source = meeting.fileName || meeting.title || "Meeting recording";
  return `
    <button class="meeting-row" type="button" data-meeting-id="${escapeHtml(meeting.meetingId)}" aria-label="Open ${escapeHtml(meeting.title || "meeting")}">
      <span class="meeting-main">
        <span class="meeting-symbol">${icons.audio}</span>
        <span class="meeting-title-wrap">
          <span class="meeting-title">${escapeHtml(meeting.title || "Untitled meeting")}</span>
          <span class="meeting-meta">${escapeHtml(source)}${duration}</span>
        </span>
      </span>
      <span class="meeting-date">${escapeHtml(toDateLabel(meeting.createdAt))}</span>
      <span class="participant-list" aria-label="${people.length} participants">${avatars}${morePeople}</span>
      <span class="meeting-state ${status.css}">${status.label}</span>
      <span class="meeting-arrow" aria-hidden="true">›</span>
    </button>`;
}

function renderMetrics() {
  const items = state.meetings;
  const ready = items.filter((meeting) => meeting.status === "READY");
  const decisions = ready.reduce((sum, meeting) => sum + (meeting.keyDecisions || []).length, 0);
  const actions = ready.reduce((sum, meeting) => sum + (meeting.actionItems || []).length, 0);
  document.querySelector("#metric-total").textContent = String(ready.length).padStart(2, "0");
  document.querySelector("#metric-decisions").textContent = String(decisions).padStart(2, "0");
  document.querySelector("#metric-actions").textContent = String(actions).padStart(2, "0");
  document.querySelector("#nav-count").textContent = String(items.length);
  const metricFooters = document.querySelectorAll(".metric-card .metric-foot");
  metricFooters[0].children[0].textContent = state.connected ? "" : "↑ 2";
  metricFooters[0].children[1].textContent = state.connected ? "in this workspace" : "vs. last week";
  metricFooters[1].children[0].textContent = state.connected ? "" : "↑ 18%";
  metricFooters[1].children[1].textContent = state.connected ? "captured so far" : "vs. last week";
  metricFooters[2].children[0].textContent = state.connected ? "" : "5 due soon";
  metricFooters[2].children[1].textContent = state.connected ? "captured so far" : "";
  document.querySelector(".focus-panel > p").innerHTML =
    `Your team made <strong>${decisions} ${decisions === 1 ? "decision" : "decisions"}</strong> across ${ready.length} analyzed ${ready.length === 1 ? "meeting" : "meetings"}. The latest conversations and next steps are ready when you are.`;
  document.querySelector(".focus-footer").innerHTML =
    `<span class="focus-check">${icons.check}</span><span><strong>${actions} action ${actions === 1 ? "item" : "items"}</strong> captured across these meetings.</span>`;
  if (state.connected) {
    document.querySelector(".time-card .metric-value").innerHTML = `—<span class="metric-unit"> hrs</span>`;
    document.querySelector(".time-card .metric-foot").firstElementChild.textContent = "Duration savings aren't tracked yet.";
  } else {
    document.querySelector(".time-card .metric-value").innerHTML = `4.2<span class="metric-unit"> hrs</span>`;
    document.querySelector(".time-card .metric-foot").firstElementChild.textContent = "That's a whole afternoon.";
  }
}

function renderActivityChart() {
  const now = new Date();
  const bucketCount = state.chartDays === 7 ? 7 : state.chartDays === 30 ? 6 : 9;
  const daysPerBucket = state.chartDays / bucketCount;
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - state.chartDays + 1);
  const days = [];
  for (let index = 0; index < bucketCount; index += 1) {
    const bucketStart = new Date(start);
    bucketStart.setDate(bucketStart.getDate() + index * daysPerBucket);
    const bucketEnd = new Date(start);
    bucketEnd.setDate(bucketEnd.getDate() + (index + 1) * daysPerBucket);
    const count = state.meetings.filter((meeting) => {
      const created = new Date(meeting.createdAt);
      return !Number.isNaN(created.getTime()) && created >= bucketStart && created < bucketEnd;
    }).length;
    days.push({ date: bucketStart, end: bucketEnd, count, today: index === bucketCount - 1 });
  }
  const maximum = Math.max(4, Math.ceil(Math.max(...days.map((day) => day.count)) / 4) * 4);
  const chartLabels = [maximum, maximum * .75, maximum * .5, maximum * .25, 0]
    .map((value) => `<span>${Number.isInteger(value) ? value : Math.round(value)}</span>`).join("");
  document.querySelector(".chart-y-labels").innerHTML = chartLabels;
  const labels = days.map((day) => `${day.date.toLocaleDateString([], { month: "short", day: "numeric" })} ${day.count}`).join(", ");
  document.querySelector("#chart-bars").setAttribute("aria-label", `Meetings in the last ${state.chartDays} days: ${labels}`);
  document.querySelector("#chart-bars").innerHTML = days.map((day) => {
    const percent = Math.max(day.count ? 5 : 0, (day.count / maximum) * 100);
    const label = state.chartDays === 7
      ? day.date.toLocaleDateString([], { weekday: "short" })
      : day.date.toLocaleDateString([], { month: "short", day: "numeric" });
    const startLabel = day.date.toLocaleDateString([], { month: "short", day: "numeric" });
    const endLabel = new Date(day.end.getTime() - 1).toLocaleDateString([], { month: "short", day: "numeric" });
    return `<button type="button" class="chart-column${day.today ? " today" : ""}${day.count === 0 ? " quiet" : ""}"
      data-range-start="${day.date.getTime()}" data-range-end="${day.end.getTime()}"
      aria-label="${startLabel}${state.chartDays > 7 ? ` through ${endLabel}` : ""}: ${day.count} meetings. Filter meeting list.">
      <span class="bar-value">${day.count}</span>
      <i style="--bar:${percent}%"></i>
      <span class="bar-label">${label}</span>
    </button>`;
  }).join("");
  document.querySelector("#chart-range").value = String(state.chartDays);
  const clearDate = document.querySelector("#clear-date-filter");
  clearDate.hidden = !state.chartRangeFilter;
  if (state.chartRangeFilter) {
    clearDate.textContent = `Date: ${state.chartRangeFilter.label} ×`;
  }
}

function renderMeetings() {
  const filtered = filteredMeetings();
  const visible = filtered.slice(0, state.visibleCount);
  elements.list.innerHTML = visible.map(renderMeeting).join("");
  elements.list.hidden = visible.length === 0;
  elements.empty.hidden = visible.length !== 0;
  elements.count.textContent = state.query
    ? `${filtered.length} ${filtered.length === 1 ? "match" : "matches"}${state.connected ? "" : " in sample meetings"}`
    : `Showing ${visible.length} of ${filtered.length} ${filtered.length === 1 ? "meeting" : "meetings"}`;
  elements.loadMore.hidden = filtered.length <= visible.length;
  renderMetrics();
  renderActivityChart();
  const counts = {
    all: state.meetings.length,
    READY: state.meetings.filter((meeting) => meeting.status === "READY").length,
    PROCESSING: state.meetings.filter((meeting) => meeting.status === "PROCESSING" || meeting.status === "UPLOADING").length,
    FAILED: state.meetings.filter((meeting) => meeting.status === "FAILED").length,
  };
  document.querySelector("#filter-all-count").textContent = counts.all;
  document.querySelector("#filter-ready-count").textContent = counts.READY;
  document.querySelector("#filter-processing-count").textContent = counts.PROCESSING;
  document.querySelector("#filter-failed-count").textContent = counts.FAILED;
}

function updateView(view) {
  state.view = view;
  document.querySelectorAll("[data-view]").forEach((button) => {
    if (button.classList.contains("nav-item")) {
      button.classList.toggle("is-active", button.dataset.view === view);
      if (button.dataset.view === view) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    }
  });
  const labels = {
    overview: ["Overview", "Recent meetings", "The conversations shaping your week."],
    meetings: ["Meetings", "All meetings", "Every conversation in your workspace."],
    decisions: ["Decisions & actions", "Open follow-ups", "Decisions and next steps captured in your meetings."],
    search: ["Search", "Search meetings", "Find a decision, a deadline, or something someone said."],
  };
  const [page, heading, description] = labels[view] || labels.overview;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  document.querySelector("#breadcrumb-current").textContent = page;
  document.querySelector("#meetings-heading").textContent = heading;
  document.querySelector("#meetings-description").textContent = description;
  document.querySelector("#page-title").innerHTML = `${view === "overview" ? `${greeting}, Alex` : escapeHtml(page)}<span class="title-period">.</span>`;
  document.querySelector("#page-subtitle").textContent = view === "overview"
    ? "A little clarity goes a long way. Here's what's happening across your meetings."
    : description;
  state.visibleCount = view === "overview" ? 5 : 50;
  renderMeetings();
  if (view === "search") elements.search.focus();
  if (view === "meetings" || view === "decisions") {
    document.querySelector("#meetings-section").scrollIntoView({ behavior: "smooth", block: "start" });
  } else {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

async function loadMeetings(query = "") {
  const requestNumber = ++state.searchRequest;
  if (!state.connected) {
    renderMeetings();
    return;
  }
  const loadingText = elements.list.innerHTML;
  if (!state.meetings.length) {
    elements.list.innerHTML = '<div class="loading-row">Looking through your meetings…</div>';
  }
  try {
    const result = await apiRequest(`/meetings${query ? `?search=${encodeURIComponent(query)}` : ""}`);
    if (requestNumber !== state.searchRequest) return;
    if (!Array.isArray(result.items)) throw new Error("The workspace returned an invalid meeting list.");
    state.meetings = result.items;
    state.visibleCount = state.view === "overview" ? 5 : 50;
    renderMeetings();
  } catch (error) {
    if (requestNumber !== state.searchRequest) return;
    if (state.meetings.length) elements.list.innerHTML = loadingText;
    else elements.list.innerHTML = `<div class="loading-row">${escapeHtml(error.message || "Could not load meetings.")}</div>`;
    if (!state.accessToken) {
      setConnection(false);
      openModal(elements.settingsModal);
    }
    showToast(error.message || "Could not load meetings.", true);
  }
}

async function showMeeting(meetingId) {
  const sample = state.meetings.find((meeting) => meeting.meetingId === meetingId);
  let meeting = sample;
  const detail = document.querySelector("#detail-content");
  detail.innerHTML = '<div class="loading-detail">Opening meeting…</div>';
  openModal(elements.detailModal);
  try {
    if (state.connected) meeting = await apiRequest(`/meetings/${encodeURIComponent(meetingId)}`);
    if (!meeting) throw new Error("This meeting is no longer available.");
    let transcript = meeting.transcript || "";
    if (state.connected && meeting.transcriptUrl) {
      const transcriptResponse = await fetch(meeting.transcriptUrl);
      if (!transcriptResponse.ok) throw new Error("The transcript could not be loaded.");
      const transcriptData = await transcriptResponse.json();
      transcript = transcriptData.text || "";
    }
    const decisions = (meeting.keyDecisions || []).map((decision) => `<li>${escapeHtml(decision)}</li>`).join("");
    const actions = (meeting.actionItems || []).map((action) => `
      <li class="action-row"><span>${escapeHtml(action.task || "Follow up")}</span><small>${escapeHtml(action.owner || "Unassigned")} · ${escapeHtml(action.due_date || "No due date")}</small></li>
    `).join("");
    const topics = (meeting.topics || []).map(escapeHtml).join(" · ");
    const mediaLink = meeting.audioUrl
      ? `<a class="button button-secondary" href="${escapeHtml(meeting.audioUrl)}" target="_blank" rel="noopener noreferrer">Listen to recording ↗</a>`
      : "";
    const status = meetingStatus(meeting.status);
    detail.innerHTML = `
      <div class="detail-kicker">MEETING NOTES</div>
      <h2 class="detail-title" id="detail-title">${escapeHtml(meeting.title || "Untitled meeting")}</h2>
      <div class="detail-meta"><span>${escapeHtml(toDateLabel(meeting.createdAt))}</span><span>${escapeHtml(meeting.fileName || "Recording")}</span><span class="meeting-state ${status.css}">${status.label}</span></div>
      <div class="detail-actions">${mediaLink}</div>
      ${meeting.summary ? `<section class="detail-section"><h3>In short</h3><p class="detail-summary">${escapeHtml(meeting.summary)}</p></section>` : ""}
      ${decisions ? `<section class="detail-section"><h3>Key decisions</h3><ul class="detail-list">${decisions}</ul></section>` : ""}
      ${actions ? `<section class="detail-section"><h3>Next steps</h3><ul class="detail-list">${actions}</ul></section>` : ""}
      ${topics ? `<section class="detail-section"><h3>Topics</h3><p class="detail-summary">${topics}</p></section>` : ""}
      ${transcript ? `<section class="detail-section"><h3>Transcript</h3><pre class="transcript-box">${escapeHtml(transcript)}</pre></section>` : ""}
      ${meeting.status === "FAILED" ? `<section class="detail-section"><h3>What happened</h3><p class="detail-summary">${escapeHtml(meeting.errorMessage || "This recording could not be processed. Check the AWS logs and try uploading it again.")}</p></section>` : ""}
      ${meeting.status !== "READY" && meeting.status !== "FAILED" ? `<p class="detail-summary">Your recording is being transcribed and analyzed. This can take a few minutes; check back shortly.</p>` : ""}
    `;
  } catch (error) {
    detail.innerHTML = `<div class="form-error">${escapeHtml(error.message || "Could not load this meeting.")}</div>`;
  }
}

function selectFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  if (!state.connected) {
    elements.input.value = "";
    showToast("Connect your AWS workspace to upload recordings.");
    openModal(elements.settingsModal);
    return;
  }
  uploadFiles(files);
}

async function uploadFiles(files) {
  const validFiles = files.filter((file) => file.size > 0 && file.size <= 500 * 1024 * 1024);
  if (!validFiles.length) {
    showToast("Choose an audio or video recording under 500 MB.", true);
    return;
  }
  const button = document.querySelector("#upload-button");
  const originalLabel = button.innerHTML;
  button.disabled = true;
  button.innerHTML = "Uploading…";
  let uploaded = 0;
  try {
    for (const file of validFiles) {
      const result = await apiRequest("/upload-url", {
        method: "POST",
        body: JSON.stringify({
          fileName: file.name,
          contentType: file.type || "application/octet-stream",
          fileSize: file.size,
        }),
      });
      const uploadResponse = await fetch(result.uploadUrl, {
        method: "PUT",
        headers: { "Content-Type": file.type || "application/octet-stream" },
        body: file,
      });
      if (!uploadResponse.ok) {
        throw new Error(`S3 could not upload ${file.name}. Please try again.`);
      }
      uploaded += 1;
    }
    showToast(`${uploaded} ${uploaded === 1 ? "recording is" : "recordings are"} uploaded. Transcription is starting.`);
    state.query = "";
    elements.search.value = "";
    await loadMeetings();
  } catch (error) {
    const message = uploaded
      ? `${uploaded} ${uploaded === 1 ? "recording was" : "recordings were"} uploaded, but the next upload failed: ${error.message || "please try again."}`
      : error.message || "The recording could not be uploaded.";
    showToast(message, true);
    await loadMeetings(state.query);
  } finally {
    button.disabled = false;
    button.innerHTML = originalLabel;
    elements.input.value = "";
  }
}

function setFilter(filter) {
  const next = filter || "all";
  state.filter = next;
  const labels = {
    all: "All meetings",
    READY: "Ready",
    PROCESSING: "Processing",
    FAILED: "Needs attention",
  };
  document.querySelector("#filter-button").innerHTML = `${icons.filter}<span>${escapeHtml(labels[next] || labels.all)}</span><span class="filter-chevron" aria-hidden="true">⌄</span>`;
  document.querySelector("#filter-button").setAttribute("aria-expanded", "false");
  document.querySelector("#filter-menu").hidden = true;
  document.querySelectorAll("[data-status-filter]").forEach((option) => {
    option.setAttribute("aria-checked", String(option.dataset.statusFilter === next));
  });
  renderMeetings();
}

function beginSecureSignIn() {
  const config = authConfig();
  if (!config.apiUrl || !config.userPoolClientId || !config.userPoolDomain || !config.region || !config.dashboardUrl) {
    showToast("Deploy the AWS workspace to enable secure account sign-in.", true);
    return;
  }
  const verifier = randomToken(48);
  const oauthState = randomToken(24);
  sessionStorage.setItem("briefly-oauth-verifier", verifier);
  sessionStorage.setItem("briefly-oauth-state", oauthState);
  crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)).then((digest) => {
    const parameters = new URLSearchParams({
      response_type: "code",
      client_id: config.userPoolClientId,
      redirect_uri: config.dashboardUrl,
      scope: "openid email profile",
      code_challenge: base64Url(new Uint8Array(digest)),
      code_challenge_method: "S256",
      state: oauthState,
    });
    window.location.assign(`https://${config.userPoolDomain}.auth.${config.region}.amazoncognito.com/oauth2/authorize?${parameters}`);
  }).catch(() => showToast("Your browser could not start a secure sign-in.", true));
}

async function finishSecureSignIn() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (!code) {
    const authError = params.get("error_description") || params.get("error");
    if (authError) {
      window.history.replaceState(null, "", window.location.pathname);
      showToast(authError, true);
    }
    return;
  }
  const expectedState = sessionStorage.getItem("briefly-oauth-state");
  const returnedState = params.get("state");
  const verifier = sessionStorage.getItem("briefly-oauth-verifier");
  if (!expectedState || expectedState !== returnedState || !verifier) {
    window.history.replaceState(null, "", window.location.pathname);
    clearSession();
    showToast("Sign-in could not be verified. Start again to protect your account.", true);
    return;
  }
  try {
    const idToken = await exchangeCodeForSession(code, verifier);
    const claims = decodeJwt(idToken);
    const email = claims.email || "Signed-in member";
    document.querySelector(".profile-copy strong").textContent = email;
    document.querySelector(".profile-avatar").textContent = initialsFor(email.split("@")[0]);
    setConnection(true);
    closeModal(elements.settingsModal);
    await loadMeetings();
    showToast("Your private workspace is ready.");
  } catch (error) {
    clearSession();
    showToast(error.message || "Secure sign-in could not be completed.", true);
    openModal(elements.settingsModal);
  }
}

document.querySelectorAll("[data-icon]").forEach((node) => {
  node.innerHTML = icons[node.dataset.icon] || "";
});

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => updateView(button.dataset.view));
});

document.querySelector("#upload-button").addEventListener("click", () => elements.input.click());
document.querySelector("#sidebar-upload").addEventListener("click", () => elements.input.click());
document.querySelector("#empty-upload").addEventListener("click", () => elements.input.click());
elements.input.addEventListener("change", () => selectFiles(elements.input.files));
document.querySelector("#settings-button").addEventListener("click", () => openModal(elements.settingsModal));
document.querySelector("#top-settings").addEventListener("click", () => openModal(elements.settingsModal));
document.querySelectorAll("[data-close-modal]").forEach((button) => {
  button.addEventListener("click", () => closeModal(button.closest(".modal-backdrop")));
});
document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
  backdrop.addEventListener("click", (event) => {
    if (event.target === backdrop) closeModal(backdrop);
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeModal(elements.settingsModal);
    closeModal(elements.detailModal);
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    elements.search.focus();
  }
});
document.querySelector("#meeting-search").addEventListener("input", (event) => {
  state.query = event.target.value.trim();
  state.visibleCount = 50;
  window.clearTimeout(state.searchTimer);
  state.searchTimer = window.setTimeout(() => loadMeetings(state.query), state.connected ? 220 : 0);
});
document.querySelector("#load-more").addEventListener("click", () => {
  state.visibleCount += 10;
  renderMeetings();
});
document.querySelector("#filter-button").addEventListener("click", () => {
  const menu = document.querySelector("#filter-menu");
  menu.hidden = !menu.hidden;
  document.querySelector("#filter-button").setAttribute("aria-expanded", String(!menu.hidden));
});
document.querySelectorAll("[data-status-filter]").forEach((option) => {
  option.addEventListener("click", () => setFilter(option.dataset.statusFilter));
});
document.querySelector("#chart-range").addEventListener("change", (event) => {
  state.chartDays = Number(event.target.value);
  state.chartRangeFilter = null;
  renderMeetings();
});
document.querySelector("#chart-bars").addEventListener("click", (event) => {
  const bar = event.target.closest("[data-range-start]");
  if (!bar) return;
  const start = Number(bar.dataset.rangeStart);
  const end = Number(bar.dataset.rangeEnd);
  const dateOptions = { month: "short", day: "numeric" };
  const label = `${new Date(start).toLocaleDateString([], dateOptions)}${state.chartDays === 7 ? "" : ` – ${new Date(end - 1).toLocaleDateString([], dateOptions)}`}`;
  state.chartRangeFilter = { start, end, label };
  state.visibleCount = 50;
  renderMeetings();
  document.querySelector("#meetings-section").scrollIntoView({ behavior: "smooth", block: "start" });
});
document.querySelector("#clear-date-filter").addEventListener("click", () => {
  state.chartRangeFilter = null;
  renderMeetings();
});
document.querySelector("#sort-button").addEventListener("click", () => {
  state.sort = state.sort === "newest" ? "oldest" : "newest";
  document.querySelector("#sort-label").textContent = state.sort === "newest" ? "Newest first" : "Oldest first";
  document.querySelector("#sort-button").title = state.sort === "newest" ? "Sort meetings by oldest first" : "Sort meetings by newest first";
  renderMeetings();
});
document.querySelector("#refresh-button").addEventListener("click", async () => {
  if (state.connected) {
    await loadMeetings(state.query);
    showToast("Your meeting list is up to date.");
  } else {
    renderMeetings();
    showToast("Sample meetings refreshed.");
  }
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".filter-wrap")) {
    document.querySelector("#filter-menu").hidden = true;
    document.querySelector("#filter-button").setAttribute("aria-expanded", "false");
  }
});
document.querySelector("#meeting-list").addEventListener("click", (event) => {
  const row = event.target.closest("[data-meeting-id]");
  if (row) showMeeting(row.dataset.meetingId);
});
document.querySelector("#connect-button").addEventListener("click", beginSecureSignIn);
document.querySelector("#disconnect-button").addEventListener("click", () => {
  clearSession();
  state.meetings = sampleMeetings;
  state.chartRangeFilter = null;
  setFilter("all");
  closeModal(elements.settingsModal);
  updateView("overview");
  showToast("Sample workspace restored.");
});
document.querySelector("#signout-button").addEventListener("click", () => {
  const config = authConfig();
  clearSession();
  if (config.userPoolDomain && config.region && config.userPoolClientId && config.dashboardUrl) {
    const logout = new URL(
      `https://${config.userPoolDomain}.auth.${config.region}.amazoncognito.com/logout`,
    );
    logout.searchParams.set("client_id", config.userPoolClientId);
    logout.searchParams.set("logout_uri", config.dashboardUrl);
    window.location.assign(logout);
  } else {
    closeModal(elements.settingsModal);
    showToast("You have signed out.");
  }
});

const dropTarget = document.querySelector(".page-content");
dropTarget.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropTarget.classList.add("is-dragging");
});
dropTarget.addEventListener("dragleave", (event) => {
  if (!dropTarget.contains(event.relatedTarget)) dropTarget.classList.remove("is-dragging");
});
dropTarget.addEventListener("drop", (event) => {
  event.preventDefault();
  dropTarget.classList.remove("is-dragging");
  selectFiles(event.dataTransfer.files);
});

setConnection(false);
document.querySelector("#today-label").textContent = new Date().toLocaleDateString("en-US", {
  weekday: "long",
  month: "long",
  day: "numeric",
}).toUpperCase();
renderMeetings();
finishSecureSignIn();
if (state.accessToken && state.refreshToken && state.apiUrl) {
  state.meetings = [];
  setConnection(true);
  loadMeetings();
}
