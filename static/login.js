function togglePassword() {
  const input = document.getElementById('password');
  const icon  = document.getElementById('eye-icon');
  const show  = input.type === 'password';
  input.type     = show ? 'text' : 'password';
  icon.className = show ? 'ti ti-eye-off' : 'ti ti-eye';
}

document.getElementById('login-form').addEventListener('submit', function () {
  const btn = document.getElementById('btn-submit');
  btn.classList.add('loading');
  btn.disabled = true;
});