(function () {
  "use strict";

  /* ---------- READ / LISTEN / WATCH TABS ---------- */
  var tabRow = document.getElementById("mdFormatTabs");
  if (tabRow) {
    tabRow.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-md-tab]");
      if (!btn) return;
      var targetId = btn.getAttribute("data-md-tab");
      tabRow.querySelectorAll(".tab-btn").forEach(function (b) {
        b.classList.toggle("active", b === btn);
      });
      document.querySelectorAll(".md-format-panel").forEach(function (panel) {
        panel.style.display = panel.id === targetId ? "" : "none";
      });
    });
  }

  /* ---------- PLAYBACK SPEED ---------- */
  document.querySelectorAll(".md-player").forEach(function (player) {
    var audio = player.querySelector("audio");
    if (!audio) return;
    player.querySelectorAll(".md-speed-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var speed = parseFloat(btn.getAttribute("data-speed"));
        audio.playbackRate = speed;
        player.querySelectorAll(".md-speed-btn").forEach(function (b) {
          b.classList.toggle("active", b === btn);
        });
      });
    });
  });

  /* ---------- SHARE ---------- */
  var dataEl = document.getElementById("morningDevotionShareData");
  var shareDialog = document.getElementById("shareDialog");
  var openShareBtn = document.getElementById("openShareBtn");
  if (!dataEl || !shareDialog || !openShareBtn) return;
  var DATA = JSON.parse(dataEl.textContent);

  function isRw() {
    return document.body.classList.contains("lang-rw");
  }

  function toast(msg) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(window.__toastT);
    window.__toastT = setTimeout(function () { el.classList.remove("show"); }, 3200);
  }

  shareDialog.addEventListener("click", function (e) {
    if (e.target === shareDialog) shareDialog.close();
  });

  var whatsappEl = document.getElementById("shareWhatsapp");
  var facebookEl = document.getElementById("shareFacebook");
  var xEl = document.getElementById("shareX");
  var telegramEl = document.getElementById("shareTelegram");
  var emailEl = document.getElementById("shareEmail");
  var copyBtn = document.getElementById("shareCopyLink");
  var moreBtn = document.getElementById("shareMore");

  function buildPlatformLinks(lang) {
    var text = DATA.text[lang] || DATA.text.en;
    var whatsappText = DATA.whatsapp[lang] || DATA.whatsapp.en;
    var email = DATA.email[lang] || DATA.email.en;

    if (whatsappEl) whatsappEl.href = "https://wa.me/?text=" + encodeURIComponent(whatsappText);
    if (facebookEl) facebookEl.href = "https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(DATA.url);
    if (xEl) xEl.href = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(text) + "&url=" + encodeURIComponent(DATA.url);
    if (telegramEl) telegramEl.href = "https://t.me/share/url?url=" + encodeURIComponent(DATA.url) + "&text=" + encodeURIComponent(text);
    if (emailEl) emailEl.href = "mailto:?subject=" + encodeURIComponent(email.subject) + "&body=" + encodeURIComponent(email.body);
  }

  openShareBtn.addEventListener("click", function () {
    buildPlatformLinks(isRw() ? "rw" : "en");
    shareDialog.showModal();
  });

  document.querySelectorAll("[data-language]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      buildPlatformLinks(btn.getAttribute("data-language") === "rw" ? "rw" : "en");
    });
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var done = function () { toast(isRw() ? "Ihuza ryakoporowe" : "Link copied"); };
      var fail = function () { toast(isRw() ? "Ntibyakunze gukoporora" : "Could not copy the link"); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(DATA.url).then(done, fail);
      } else {
        var input = document.createElement("textarea");
        input.value = DATA.url;
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.appendChild(input);
        input.select();
        try {
          document.execCommand("copy") ? done() : fail();
        } catch (e) {
          fail();
        }
        document.body.removeChild(input);
      }
    });
  }

  if (moreBtn) {
    if (navigator.share) {
      moreBtn.hidden = false;
      moreBtn.addEventListener("click", function () {
        var lang = isRw() ? "rw" : "en";
        navigator.share({
          title: DATA.text[lang] || DATA.text.en,
          text: DATA.text[lang] || DATA.text.en,
          url: DATA.url,
        }).catch(function () {});
      });
    } else {
      moreBtn.hidden = true;
    }
  }
})();
