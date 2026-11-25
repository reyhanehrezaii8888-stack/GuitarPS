/* ============================================================
   GuitarPS — shared front-end script
   همهٔ صفحات از این فایل استفاده می‌کنند؛ هر بخش با بررسی وجود
   المان کار می‌کند تا در صفحه‌هایی که فرم نیست خطا ندهد.
   ============================================================ */

const API_BASE = 'https://app.guitarreyhane.ir';
const TOKEN_KEY = 'guitarps_access_token';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

/* ---------- منوی موبایل ---------- */
function closeMenu() {
  const links = $('.links');
  if (links) links.classList.remove('open');
}

/* ---------- مودال ورود / ثبت‌نام ---------- */
function openAuth() {
  const modal = $('#auth-modal');
  if (!modal) return;
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
  const phone = $('#phone');
  if (phone) setTimeout(() => phone.focus(), 80);
}

function closeAuth() {
  const modal = $('#auth-modal');
  if (!modal) return;
  modal.classList.remove('show');
  document.body.style.overflow = '';
}

/* ---------- توست ---------- */
let toastTimer = null;
function toast(msg) {
  const t = $('#toast');
  if (!t) return;
  t.textContent = msg;
  t.style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.style.display = 'none'), 3600);
}

/* ---------- راه‌اندازی عمومی ---------- */
document.addEventListener('DOMContentLoaded', () => {
  /* چیپ‌های نمونه سؤال */
  $$('.chip').forEach((btn) => {
    btn.addEventListener('click', () => {
      const ta = $('#challenge');
      if (!ta) return;
      ta.value = btn.textContent.trim();
      ta.focus();
    });
  });

  /* آکاردئون سوالات متداول */
  $$('.faq-q').forEach((btn) => {
    btn.addEventListener('click', () => btn.parentElement.classList.toggle('open'));
  });

  /* بستن منو بعد از کلیک روی لینک */
  $$('.links a').forEach((a) => a.addEventListener('click', closeMenu));

  /* بستن مودال با کلیک بیرون و کلید Esc */
  const modal = $('#auth-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target.id === 'auth-modal') closeAuth();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAuth();
  });

  initAnalyze();
  initOtp();
  initContactForm();
  markActiveNav();
});

/* ---------- فرم تحلیل چالش ---------- */
function initAnalyze() {
  const btn = $('#analyze');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const ta = $('#challenge');
    const result = $('#form-result');
    const text = ta.value.trim();

    if (!text) {
      ta.focus();
      ta.style.borderColor = '#d44867';
      return;
    }
    ta.style.borderColor = '';

    btn.disabled = true;
    btn.textContent = 'در حال آماده‌سازی…';

    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = 'تحلیل رایگان چالش <span>←</span>';
      if (result) {
        result.style.display = 'block';
        result.innerHTML =
          'برای حفظ چالشت، متن فرم نگه داشته شد. برای دریافت تحلیل اختصاصی، شماره موبایلت را با کد یک‌بارمصرف تایید کن.';
      }
      openAuth();
    }, 650);
  });
}

/* ---------- جریان OTP ---------- */
function initOtp() {
  const requestBtn = $('#request-otp');
  const verifyBtn = $('#verify-otp');
  const backBtn = $('#back-phone');

  if (requestBtn) {
    requestBtn.addEventListener('click', async () => {
      const phone = $('#phone').value.trim();
      const msg = $('#phone-msg');
      if (!/^09\d{9}$/.test(phone)) {
        msg.textContent = 'شماره موبایل معتبر وارد کن.';
        return;
      }
      msg.textContent = 'در حال ارسال کد…';
      try {
        const r = await fetch(API_BASE + '/api/auth/otp/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || d.message || 'ارسال کد ناموفق بود.');
        $('#step-phone').classList.remove('active');
        $('#step-otp').classList.add('active');
        $('#auth-desc').textContent = 'کد تایید ارسال‌شده به ' + phone + ' را وارد کن.';
        $('#otp').focus();
      } catch (e) {
        msg.textContent =
          e.message === 'Failed to fetch'
            ? 'اتصال به سرویس احراز هویت برقرار نشد؛ مطمئن شو API در دسترس است.'
            : e.message;
      }
    });
  }

  if (verifyBtn) {
    verifyBtn.addEventListener('click', async () => {
      const phone = $('#phone').value.trim();
      const otp = $('#otp').value.trim();
      const msg = $('#otp-msg');
      if (!otp) {
        msg.textContent = 'کد پیامکی را وارد کن.';
        return;
      }
      msg.textContent = 'در حال بررسی کد…';
      try {
        const r = await fetch(API_BASE + '/api/auth/otp/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, otp }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.detail || d.message || 'کد تایید معتبر نیست.');

        const token = d.access_token || d.token;
        if (token) localStorage.setItem(TOKEN_KEY, token);

        closeAuth();
        toast('ورود با موفقیت انجام شد.');
        const result = $('#form-result');
        const ta = $('#challenge');
        if (result && ta && ta.value.trim()) {
          result.textContent = 'حساب تایید شد. چالش شما برای دریافت تحلیل حفظ شده است.';
        }
      } catch (e) {
        msg.textContent =
          e.message === 'Failed to fetch'
            ? 'اتصال به سرویس تایید برقرار نشد؛ مطمئن شو API در دسترس است.'
            : e.message;
      }
    });
  }

  if (backBtn) {
    backBtn.addEventListener('click', () => {
      $('#step-otp').classList.remove('active');
      $('#step-phone').classList.add('active');
      $('#auth-desc').textContent = 'شماره موبایلت را وارد کن تا کد تایید برایت پیامک شود.';
    });
  }
}

/* ---------- فرم تماس (بدون بک‌اند: mailto) ---------- */
function initContactForm() {
  const form = $('#contact-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = $('#c-name').value.trim();
    const email = $('#c-email').value.trim();
    const subject = $('#c-subject').value.trim();
    const body = $('#c-body').value.trim();
    const note = $('#contact-note');

    if (!name || !body) {
      note.textContent = 'نام و متن پیام را کامل کن.';
      note.style.color = '#ba3152';
      return;
    }

    const mail =
      'mailto:hello@guitarreyhane.ir' +
      '?subject=' + encodeURIComponent((subject || 'پیام از سایت GuitarPS') + ' — ' + name) +
      '&body=' + encodeURIComponent(body + '\n\n' + name + (email ? ' | ' + email : ''));

    window.location.href = mail;
    note.textContent = 'در حال باز کردن برنامهٔ ایمیل… اگر باز نشد، مستقیم به hello@guitarreyhane.ir بنویس.';
    note.style.color = '#208768';
  });
}

/* ---------- فعال‌کردن لینک صفحهٔ جاری در منو ---------- */
function markActiveNav() {
  const here = location.pathname.split('/').pop() || 'index.html';
  $$('.links a').forEach((a) => {
    const href = a.getAttribute('href') || '';
    if (href === here) a.style.color = 'var(--p)';
  });
}
