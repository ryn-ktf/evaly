// search stuff
const search_btn = document.getElementById('search_btn');
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



// view all courses btn
document.getElementById('view_all_btn').addEventListener('click', () => {
  alert('Navigating to all courses page');
});

// contact form
document.getElementById('fb_send_btn').addEventListener('click', () => {
  const n = document.getElementById('fb_name').value.trim();
  const em = document.getElementById('fb_email').value.trim();
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

  alert(`Message sent! Thank you, ${n}. We'll get back to you at ${em}.`);
  document.getElementById('fb_name').value = '';
  document.getElementById('fb_email').value = '';
  document.getElementById('fb_subject').value = '';
  document.getElementById('fb_msg').value = '';
});

// --- stats count up animation on scroll ---
let stats_done = false;

function doCountUp(el, target, suffix) {
  let current = 0;
  const duration = 1800;
  const stepTime = 16;
  const steps = duration / stepTime;
  const increment = target / steps;

  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    if (target >= 1000) {
      el.textContent = (current >= 1000 ? (current / 1000).toFixed(1) + 'k' : Math.floor(current)) + suffix;
    } else {
      el.textContent = Math.floor(current) + suffix;
    }
  }, stepTime);
}

function checkIfStatsVisible() {
  if (stats_done) return;
  const statsBox = document.getElementById('stats_section');
  const rect = statsBox.getBoundingClientRect();
  if (rect.top < window.innerHeight - 80) {
    stats_done = true;
    doCountUp(document.getElementById('stat_courses'), 2400, '+');
    doCountUp(document.getElementById('stat_students'), 18000, '+');
    doCountUp(document.getElementById('stat_teachers'), 340, '+');
  }
}

window.addEventListener('scroll', checkIfStatsVisible);
checkIfStatsVisible();