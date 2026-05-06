// ── config ──────────────────────────────────────────────────────────────────
// change this to your Render URL once deployed, e.g. https://evaly-api.onrender.com
const API_BASE = 'https://evaly-api.onrender.com/api';
// ── search ──────────────────────────────────────────────────────────────────
const search_btn   = document.getElementById('search_btn');
const search_input = document.getElementById('search_input');

search_btn.addEventListener('click', () => {
  const q = search_input.value.trim();
  if (q) {
    alert(`Searching for: "${q}"`);
  } else {
    search_input.focus();
  }
});

search_input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') search_btn.click();
});

// ── play buttons ─────────────────────────────────────────────────────────────
document.querySelectorAll('.play_btn').forEach(btn => {
  btn.addEventListener('click', () => {
    alert(`Opening video: ${btn.dataset.video}`);
  });
});

// ── view all courses ─────────────────────────────────────────────────────────
document.getElementById('view_all_btn').addEventListener('click', () => {
  window.location.href = 'quiz.html';
});

// ── contact form → POST /api/contact/ ────────────────────────────────────────
document.getElementById('fb_send_btn').addEventListener('click', async () => {
  const n   = document.getElementById('fb_name').value.trim();
  const em  = document.getElementById('fb_email').value.trim();
  const sub = document.getElementById('fb_subject').value.trim();
  const msg = document.getElementById('fb_msg').value.trim();

  if (!n || !em || !sub || !msg) {
    alert('Please fill in all fields before sending.');
    return;
  }

  const emailCheck = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailCheck.test(em)) {
    alert('Please enter a valid email address.');
    return;
  }

  const send_btn = document.getElementById('fb_send_btn');
  send_btn.disabled = true;
  send_btn.textContent = 'Sending...';

  try {
    const res = await fetch(`${API_BASE}/contact/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: n, email: em, subject: sub, message: msg }),
    });

    const data = await res.json();

    if (res.ok) {
      alert(data.message);
      document.getElementById('fb_name').value    = '';
      document.getElementById('fb_email').value   = '';
      document.getElementById('fb_subject').value = '';
      document.getElementById('fb_msg').value     = '';
    } else {
      const err_msg = typeof data.detail === 'string'
        ? data.detail
        : data.detail?.[0]?.msg ?? 'Something went wrong.';
      alert(`Error: ${err_msg}`);
    }
  } catch (err) {
    alert('Could not reach the server. Please try again later.');
    console.error(err);
  } finally {
    send_btn.disabled = false;
    send_btn.textContent = 'Send message';
  }
}); 

// ── stats count-up on scroll ─────────────────────────────────────────────────
// ── stats count-up on scroll ─────────────────────────────────────────
let stats_done = false;

function doCountUp(el, target, suffix) {
  let current = 0;
  const stepTime = 16;
  const duration = 1500;
  const steps = duration / stepTime;
  const increment = target / steps;

  const timer = setInterval(() => {
    current += increment;

    if (current >= target) {
      current = target;
      clearInterval(timer);
    }

    if (target >= 1000) {
      el.textContent =
        (current >= 1000
          ? (current / 1000).toFixed(1) + 'k'
          : Math.floor(current)) + suffix;
    } else {
      el.textContent = Math.floor(current) + suffix;
    }

  }, stepTime);
}

function checkIfStatsVisible() {
  if (stats_done) return;

  const statsBox = document.getElementById('stats_section');
  if (!statsBox) return; // safety

  const rect = statsBox.getBoundingClientRect();

  if (rect.top < window.innerHeight - 100) {
    stats_done = true;

    doCountUp(document.getElementById('stat_courses'), 2400, '+');
    doCountUp(document.getElementById('stat_students'), 18000, '+');
    doCountUp(document.getElementById('stat_teachers'), 340, '+');
  }
}

window.addEventListener('scroll', checkIfStatsVisible);
window.addEventListener('load', checkIfStatsVisible);