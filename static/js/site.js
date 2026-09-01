(function () {
  "use strict";

  var CONFIG = window.YTR_CONFIG || {};

  /* ---------- YEAR ---------- */
  ["yr", "yr2"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.textContent = new Date().getFullYear();
  });

  /* ---------- MOBILE MENU ---------- */
  var menuToggle = document.getElementById("menuToggle");
  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      var nav = document.getElementById("navLinks");
      var open = nav.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", open);
    });
    document.querySelectorAll("#navLinks a").forEach(function (link) {
      link.addEventListener("click", function () {
        document.getElementById("navLinks").classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- LANGUAGE TOGGLE (instant, client-side, persisted) ---------- */
  function setLang(lang) {
    document.body.classList.toggle("lang-rw", lang === "rw");
    document.querySelectorAll("[data-language]").forEach(function (button) {
      var active = button.getAttribute("data-language") === lang;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", active);
    });
    try {
      localStorage.setItem("ytr_lang", lang);
    } catch (e) {}
  }
  document.querySelectorAll("[data-language]").forEach(function (button) {
    button.addEventListener("click", function () { setLang(button.getAttribute("data-language")); });
  });
  try {
    var saved = localStorage.getItem("ytr_lang");
    if (saved) setLang(saved);
  } catch (e) {}

  /* ---------- HERO EMBERS ---------- */
  (function emberField() {
    var host = document.getElementById("emberField");
    if (!host) return;
    host.style.position = "absolute";
    host.style.inset = "0";
    host.style.overflow = "hidden";
    host.style.pointerEvents = "none";
    for (var i = 0; i < 10; i++) {
      var p = document.createElement("span");
      p.className = "ember-particle";
      var size = 3 + Math.random() * 4;
      p.style.width = size + "px";
      p.style.height = size + "px";
      p.style.left = 10 + Math.random() * 80 + "%";
      p.style.animationDelay = Math.random() * 7 + "s";
      p.style.animationDuration = 6 + Math.random() * 4 + "s";
      host.appendChild(p);
    }
  })();

  /* ---------- MOMENT PILLS ---------- */
  (function momentCycle() {
    var pills = document.querySelectorAll(".moment-pill");
    if (!pills.length) return;
    var i = 0;
    function tick() {
      pills.forEach(function (p) { p.classList.remove("on"); });
      pills[i].classList.add("on");
      i = (i + 1) % pills.length;
    }
    tick();
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setInterval(tick, 2600);
    }
  })();

  /* ---------- CALENDAR LINK ---------- */
  (function calLink() {
    var link = document.getElementById("calLink");
    if (!link) return;
    var title = link.getAttribute("data-title");
    var location = link.getAttribute("data-location");
    var start = link.getAttribute("data-start");
    var end = link.getAttribute("data-end");
    if (!title || !start || !end) return;
    var url =
      "https://calendar.google.com/calendar/render?action=TEMPLATE&text=" +
      encodeURIComponent(title) +
      "&dates=" + start + "/" + end +
      "&location=" + encodeURIComponent(location || "");
    link.href = url;
  })();

  /* ---------- TOAST ---------- */
  function toast(msg) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(window.__toastT);
    window.__toastT = setTimeout(function () { el.classList.remove("show"); }, 3200);
  }
  function isRw() {
    return document.body.classList.contains("lang-rw");
  }

  /* ---------- PODCAST TABS ---------- */
  var podTabs = document.getElementById("podTabs");
  if (podTabs) {
    podTabs.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-pod-tab]");
      if (!btn) return;
      var targetId = btn.getAttribute("data-pod-tab");
      podTabs.querySelectorAll(".tab-btn").forEach(function (b) {
        b.classList.toggle("active", b === btn);
      });
      document.querySelectorAll("#podBody .pod-layout").forEach(function (panel) {
        panel.style.display = panel.id === targetId ? "" : "none";
      });
    });
  }

  /* ---------- VIDEO CLICK TOASTS ---------- */
  var featuredVideo = document.getElementById("featuredVideo");
  if (featuredVideo) {
    featuredVideo.addEventListener("click", function () {
      var youtube = featuredVideo.getAttribute("data-youtube");
      if (youtube) {
        window.open(youtube, "_blank", "noopener");
        return;
      }
      var t = document.getElementById("vidToast");
      if (t) {
        t.classList.add("show");
        setTimeout(function () { t.classList.remove("show"); }, 2200);
      }
    });
  }
  document.querySelectorAll(".vid-thumb").forEach(function (thumb) {
    thumb.addEventListener("click", function () {
      var youtube = thumb.getAttribute("data-youtube");
      if (youtube) window.open(youtube, "_blank", "noopener");
    });
  });

  /* ---------- FAQ MARQUEE NAV ---------- */
  var faqTrack = document.getElementById("faqTrack");
  var faqPrev = document.getElementById("faqPrev");
  var faqNext = document.getElementById("faqNext");
  if (faqTrack && faqPrev) {
    faqPrev.addEventListener("click", function () {
      faqTrack.scrollBy({ left: -320, behavior: "smooth" });
    });
  }
  if (faqTrack && faqNext) {
    faqNext.addEventListener("click", function () {
      faqTrack.scrollBy({ left: 320, behavior: "smooth" });
    });
  }

  /* ---------- SHARE / REPOST DEVOTION IMAGE ---------- */
  var shareDevoBtn = document.getElementById("shareDevoBtn");
  if (shareDevoBtn) {
    shareDevoBtn.addEventListener("click", function () {
      var card = document.getElementById("devoCard");
      var ref = (card && card.getAttribute("data-ref")) || "";
      var verse = (card && card.getAttribute("data-verse-en")) || "";
      var reflection = (card && card.getAttribute("data-reflection-en")) || "";

      var canvas = document.createElement("canvas");
      canvas.width = 1080;
      canvas.height = 1080;
      var ctx = canvas.getContext("2d");
      var grad = ctx.createLinearGradient(0, 0, 0, 1080);
      grad.addColorStop(0, "#1A1230");
      grad.addColorStop(0.6, "#2B1D46");
      grad.addColorStop(1, "#7A3A3A");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 1080, 1080);

      ctx.fillStyle = "#F6B93B";
      ctx.font = "600 46px Georgia, serif";
      ctx.fillText(ref, 90, 200);

      ctx.fillStyle = "#FBF7F0";
      ctx.font = "italic 34px Georgia, serif";
      wrapText(ctx, verse, 90, 300, 900, 46);

      ctx.fillStyle = "rgba(251,247,240,0.8)";
      ctx.font = "26px Arial, sans-serif";
      wrapText(ctx, reflection, 90, 520, 900, 40);

      ctx.fillStyle = "#F6B93B";
      ctx.font = "600 30px Arial, sans-serif";
      ctx.fillText("YOUTH TIME REVIVAL", 90, 980);
      ctx.fillStyle = "rgba(251,247,240,0.7)";
      ctx.font = "24px Arial, sans-serif";
      ctx.fillText("Today's Devotion", 90, 1020);

      function wrapText(ctx2, text, x, y, maxWidth, lineHeight) {
        var words = (text || "").split(" ");
        var line = "";
        var yy = y;
        for (var n = 0; n < words.length; n++) {
          var test = line + words[n] + " ";
          if (ctx2.measureText(test).width > maxWidth && n > 0) {
            ctx2.fillText(line, x, yy);
            line = words[n] + " ";
            yy += lineHeight;
          } else {
            line = test;
          }
        }
        ctx2.fillText(line, x, yy);
      }

      canvas.toBlob(function (blob) {
        if (!blob) {
          toast(isRw() ? "Ntibyakunze kubika." : "Could not create the image.");
          return;
        }
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "ytr-devotion.png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
        toast(isRw() ? "Byabitswe neza!" : "Saved — share away!");
      }, "image/png");
    });
  }

  /* ---------- SEARCH OVERLAY ---------- */
  var searchOverlay = document.getElementById("searchOverlay");
  var searchOpen = document.getElementById("searchOpen");
  var searchClose = document.getElementById("searchClose");
  var searchInput = document.getElementById("searchInput");
  var searchResults = document.getElementById("searchResults");

  if (searchOpen) {
    searchOpen.addEventListener("click", function () {
      searchOverlay.classList.add("open");
      searchInput.value = "";
      searchResults.innerHTML = "";
      setTimeout(function () { searchInput.focus(); }, 50);
    });
  }
  if (searchClose) {
    searchClose.addEventListener("click", function () {
      searchOverlay.classList.remove("open");
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && searchOverlay) searchOverlay.classList.remove("open");
  });

  var searchDebounce;
  if (searchInput) {
    searchInput.addEventListener("input", function (e) {
      var q = e.target.value.trim();
      clearTimeout(searchDebounce);
      if (!q) {
        searchResults.innerHTML = "";
        return;
      }
      searchDebounce = setTimeout(function () {
        var url = (CONFIG.searchUrl || "/search/") + "?q=" + encodeURIComponent(q);
        fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            var results = data.results || [];
            if (!results.length) {
              searchResults.innerHTML =
                '<p style="color:rgba(246,239,224,0.6); padding-top:20px">No results.</p>';
              return;
            }
            searchResults.innerHTML = results
              .map(function (r) {
                var title = isRw() ? r.title_rw : r.title_en;
                return (
                  '<button data-url="' + r.url + '"><span class="kind">' +
                  r.kind + "</span>" + title + "</button>"
                );
              })
              .join("");
          })
          .catch(function () {
            searchResults.innerHTML =
              '<p style="color:rgba(246,239,224,0.6); padding-top:20px">Search is unavailable right now.</p>';
          });
      }, 200);
    });
  }
  if (searchResults) {
    searchResults.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-url]");
      if (!btn) return;
      window.location.href = btn.getAttribute("data-url");
    });
  }
})();
