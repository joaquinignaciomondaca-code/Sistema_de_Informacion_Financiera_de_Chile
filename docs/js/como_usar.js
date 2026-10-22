/* Cómo usar: dos audiencias, un mismo dato.
 *
 * Las pestañas de dentro de la pestaña Información. Se mantienen en HTML puro
 * con role="tab" y aria-controls, igual que el panel superior, para que el
 * teclado y los lectores de pantalla funcionen sin lógica extra: aquí sólo se
 * alterna `hidden`, `aria-selected` y la clase activa.
 *
 * El estado inicial lo fija el marcado (humanos visible, agentes oculto), así
 * que si este archivo no carga la sección sigue siendo legible: es una mejora,
 * no un requisito para leer el contenido.
 */
(function () {
  "use strict";

  var botones = Array.prototype.slice.call(document.querySelectorAll("[data-uso-tab]"));
  if (!botones.length) return;

  var paneles = botones.map(function (boton) {
    return document.getElementById(boton.getAttribute("aria-controls"));
  });

  function activar(indice, enfocar) {
    botones.forEach(function (boton, i) {
      var activo = i === indice;
      boton.classList.toggle("active", activo);
      boton.setAttribute("aria-selected", activo ? "true" : "false");
      boton.setAttribute("tabindex", activo ? "0" : "-1");
      if (paneles[i]) paneles[i].hidden = !activo;
    });
    if (enfocar && botones[indice]) botones[indice].focus();
  }

  botones.forEach(function (boton, i) {
    boton.addEventListener("click", function () { activar(i, false); });
    boton.addEventListener("keydown", function (evento) {
      var destino = null;
      if (evento.key === "ArrowRight" || evento.key === "ArrowDown") destino = (i + 1) % botones.length;
      if (evento.key === "ArrowLeft" || evento.key === "ArrowUp") destino = (i - 1 + botones.length) % botones.length;
      if (evento.key === "Home") destino = 0;
      if (evento.key === "End") destino = botones.length - 1;
      if (destino === null) return;
      evento.preventDefault();
      activar(destino, true);
    });
  });

  /* Enlace directo: #como-usar-agentes abre la Guía en esa sub-pestaña. Sirve
   * para mandar a alguien (o a un agente) exactamente a las instrucciones que
   * necesita, sin obligarle a buscar la pestaña. */
  var hash = (window.location.hash || "").replace("#", "");
  var pedido = hash.indexOf("como-usar-") === 0 ? hash.slice("como-usar-".length) : null;
  var inicial = botones.findIndex(function (boton) {
    return boton.getAttribute("data-uso-tab") === pedido;
  });
  activar(inicial >= 0 ? inicial : 0, false);

  /* El cambio de pestaña se hace al final de la carga, no aquí: `switchMainTab`
   * lo define el script en línea de index.html y, según el orden en que el
   * navegador ejecute los diferidos, puede no existir todavía. Al llegar a
   * `load` existe seguro, y este enlace gana a la pestaña recordada. */
  if (pedido || hash === "guia") {
    var entrar = function () {
      if (typeof window.switchMainTab === "function") window.switchMainTab("guia");
    };
    if (document.readyState === "complete") entrar();
    else window.addEventListener("load", entrar);
  }

  window.SIFComoUsar = { activar: activar };
})();
