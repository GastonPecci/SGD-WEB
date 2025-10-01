document.addEventListener("DOMContentLoaded", function () {
    const mensajes = window._flashed_messages || [];
    if (mensajes && mensajes.length > 0) {
      const modalElement = document.getElementById('mensajeModal');
      const contenido = document.getElementById('mensajeContenido');
      contenido.innerHTML = mensajes.map(m => `<p>${m}</p>`).join('');
      const modal = new bootstrap.Modal(modalElement);
      modal.show();
    }
  });
  document.addEventListener("DOMContentLoaded", () => {
    const togglePassword = document.getElementById("togglePassword");
    const passwordInput = document.getElementById("password");

    togglePassword.addEventListener("click", () => {
        const isPassword = passwordInput.getAttribute("type") === "password";
        passwordInput.setAttribute("type", isPassword ? "text" : "password");
        togglePassword.textContent = isPassword ? "🙈" : "👁️"; 
    });
});