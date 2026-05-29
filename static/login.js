document.getElementById('login-form').addEventListener('submit', function () {
  const sessionid = document.getElementById('sessionid').value.trim();
  if (!sessionid) {
    return;
  }

  const btn = document.getElementById('btn-submit');
  btn.classList.add('loading');
  btn.disabled = true;
});
