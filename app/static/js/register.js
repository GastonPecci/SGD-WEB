document.addEventListener("DOMContentLoaded", () => {
    const togglePassword = document.getElementById("togglePassword");
    const passwordInput = document.getElementById("password");

    togglePassword.addEventListener("click", () => {
        const isPassword = passwordInput.getAttribute("type") === "password";
        passwordInput.setAttribute("type", isPassword ? "text" : "password");
        togglePassword.textContent = isPassword ? "🙈" : "👁️"; 
    });
});
  document.addEventListener("DOMContentLoaded", function () {
  const mensajes = window._flashed_messages || [];
  if (mensajes.length > 0) {
    const modalElement = document.getElementById('mensajeModal');
    const contenido = document.getElementById('mensajeContenido');
    
    // Insertar mensajes con estilo
    contenido.innerHTML = mensajes.map(m => `<div class="mb-2">${m}</div>`).join('');
    
    // Mostrar modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
  }
});
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("form-register");
    const btn = document.getElementById("btn-register");

    form.addEventListener("submit", function () {
        btn.disabled = true;               // 🔒 deshabilita el botón
        btn.innerText = "Procesando...";   // cambia el texto
    });
});