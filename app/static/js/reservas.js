// static/js/reservas.js
(function(){
  const HORAS_TODAS = ['14:00','15:00','16:00','17:00','18:00','19:00','20:00','21:00','22:00','23:00','00:00','01:00'];

  async function actualizarHoras() {
    try {
      const canchaElem = document.getElementById('cancha_id');
      const fechaElem = document.getElementById('fecha');
      if (!canchaElem || !fechaElem) return;

      const canchaId = canchaElem.value;
      const fecha = fechaElem.value;
      if (!canchaId || !fecha) return;

      const response = await fetch('/horas_disponibles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cancha_id: canchaId, fecha: fecha })
      });

      if (!response.ok) return;
      const ocupadas = await response.json();

      const grid = document.getElementById('grid-horas');
      if (!grid) return;
      grid.innerHTML = '';

      const horaInput = document.getElementById('hora_input');
      if (horaInput) horaInput.value = '';

      const btnReservar = document.getElementById('btn-reservar');
      if (btnReservar) btnReservar.disabled = true;

      HORAS_TODAS.forEach(hora => {
        const btn = document.createElement('button');
        btn.textContent = hora;
        btn.type = 'button';
        btn.classList.add('btn','btn-sm','px-3');

        if (Array.isArray(ocupadas) && ocupadas.includes(hora)) {
          btn.classList.add('btn-secondary');
          btn.disabled = true;
        } else {
          btn.classList.add('btn-outline-success');
          btn.addEventListener('click', () => {
            document.querySelectorAll('#grid-horas .btn-outline-success').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (horaInput) horaInput.value = hora;
            if (btnReservar) btnReservar.disabled = false;
          });
        }
        grid.appendChild(btn);
      });
    } catch (err) {
      // Mantener un log en consola solo para debugging (podés quitarlo en producción)
      console.error('actualizarHoras error:', err);
    }
  }

  // Exponer la función para usarla desde el HTML (onchange)
  window.actualizarHoras = actualizarHoras;

  // Código que se ejecuta cuando el DOM esté listo
  document.addEventListener('DOMContentLoaded', function () {

    // Modal: armar action del formEliminarReserva
    try {
      const modal = document.getElementById('modalEliminarReserva');
      const form = document.getElementById('formEliminarReserva');
      if (modal && form) {
        modal.addEventListener('show.bs.modal', function (event) {
          const button = event.relatedTarget;
          if (!button) return;
          const userId = button.getAttribute('data-user') || button.dataset.user;
          const canchaId = button.getAttribute('data-cancha') || button.dataset.cancha;
          const fecha = button.getAttribute('data-fecha') || button.dataset.fecha;
          if (userId && canchaId && fecha) {
            form.action = `/reservas/eliminar/${userId}/${canchaId}/${fecha}`;
          }
        });
      }
    } catch (e) {
      console.error('modalEliminarReserva init error', e);
    }

    // Mensajes flash (la plantilla debe definir window._flashed_messages)
    try {
      const mensajes = window._flashed_messages || [];
      if (mensajes.length > 0) {
        const modalElement = document.getElementById('mensajeModal');
        const contenido = document.getElementById('mensajeContenido');
        if (modalElement && contenido) {
          contenido.innerHTML = mensajes.map(m => `<p>${m}</p>`).join('');
          try { new bootstrap.Modal(modalElement).show(); } catch (err) { console.warn('bootstrap modal show falló', err); }
        }
      }
    } catch (e) {
      console.error('flash messages error', e);
    }

    // Desactivar botón al enviar reserva
    try {
      const formReserva = document.getElementById('form-reserva');
      const btnReserva = document.getElementById('btn-reservar');
      if (formReserva && btnReserva) {
        formReserva.addEventListener('submit', function () {
          try {
            btnReserva.disabled = true;
            btnReserva.innerText = 'Procesando...';
          } catch (err) {}
        });
      }
    } catch (e) {
      console.error('form submit init error', e);
    }

    // Check de sesión periódica
    try {
      setInterval(async () => {
        try {
          const res = await fetch('/api/check_session');
          if (!res.ok) return;
          const data = await res.json();
          if (!data.valid) {
            const modalElement = document.getElementById('mensajeModal');
            const contenido = document.getElementById('mensajeContenido');
            if (contenido) {
              contenido.innerHTML = `<div class="text-center">
                <i class="bi bi-exclamation-triangle-fill text-warning" style="font-size:2rem;"></i>
                <p class="mt-3">Tu sesión fue cerrada porque iniciaste en otro dispositivo.</p>
              </div>`;
            }
            if (modalElement) {
              try { new bootstrap.Modal(modalElement).show(); } catch (err) {}
            }
            setTimeout(() => { window.location.href = '/login'; }, 3000);
          }
        } catch (err) { console.error('check_session error', err); }
      }, 5000);
    } catch (e) {
      console.error('init check_session error', e);
    }

  }); // end DOMContentLoaded

})(); // end IIFE
