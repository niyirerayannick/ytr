/* Pause decorative animation when it cannot be seen. CSS owns motion preferences. */
(function () {
  "use strict";
  var hero = document.querySelector(".hero-spiritual");
  if (!hero) return;
  var visible = true;
  function update() {
    hero.classList.toggle("hero-motion-paused", !visible || document.hidden);
  }
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      update();
    }).observe(hero);
  }
  document.addEventListener("visibilitychange", update);
  update();
})();
