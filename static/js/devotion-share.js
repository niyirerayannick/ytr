(function () {
  "use strict";

  var dataEl = document.getElementById("devotionShareData");
  if (!dataEl) return;
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

  var shareDialog = document.getElementById("shareDialog");
  var repostDialog = document.getElementById("repostDialog");
  var openShareBtn = document.getElementById("openShareBtn");
  if (!shareDialog || !openShareBtn) return;

  /* ---------- dialog open/close (native <dialog>: Escape + focus trap are free) ---------- */
  function closeOnBackdropClick(dialog) {
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) dialog.close();
    });
  }
  closeOnBackdropClick(shareDialog);
  if (repostDialog) closeOnBackdropClick(repostDialog);

  openShareBtn.addEventListener("click", function () {
    buildPlatformLinks(isRw() ? "rw" : "en");
    shareDialog.showModal();
  });

  /* ---------- rebuild share links for the current language ---------- */
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

  // Keep links correct if the visitor flips the site language while the
  // dialog happens to be open (the toggle is instant/client-side sitewide).
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

  /* ---------- repost preview: language selection ---------- */
  if (!repostDialog) return;

  var createRepostBtn = document.getElementById("createRepostBtn");
  var repostImage = document.getElementById("repostImage");
  var repostLoading = document.getElementById("repostLoading");
  var repostShareBtn = document.getElementById("repostShareBtn");
  var repostSaveBtn = document.getElementById("repostSaveBtn");
  var rwUnavailableNote = document.getElementById("rwUnavailableNote");
  var repostLangBtns = document.querySelectorAll("[data-repost-lang]");

  var currentLang = isRw() && DATA.has_rw ? "rw" : "en";
  var currentBlob = null;
  var currentObjectUrl = null;

  function setRepostLang(lang, groupSelector) {
    if (lang === "rw" && !DATA.has_rw) return;
    currentLang = lang;
    document.querySelectorAll(groupSelector + ' [data-repost-lang]').forEach(function (btn) {
      var active = btn.getAttribute("data-repost-lang") === lang;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", active);
    });
  }

  repostLangBtns.forEach(function (btn) {
    var lang = btn.getAttribute("data-repost-lang");
    if (lang === "rw" && !DATA.has_rw) {
      btn.disabled = true;
      btn.setAttribute("aria-disabled", "true");
    }
    btn.addEventListener("click", function () {
      var dialogEl = btn.closest("dialog");
      var scope = dialogEl === repostDialog ? "#repostDialog" : "#shareDialog";
      setRepostLang(lang, scope);
      if (dialogEl === repostDialog) loadRepostImage();
    });
  });

  if (rwUnavailableNote) rwUnavailableNote.hidden = DATA.has_rw;

  function loadRepostImage() {
    if (repostLoading) repostLoading.hidden = false;
    if (repostImage) repostImage.style.opacity = "0.35";
    var url = DATA.share_image_base + "?lang=" + currentLang + "&format=square";
    fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error("share image request failed");
        return r.blob();
      })
      .then(function (blob) {
        currentBlob = blob;
        if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
        currentObjectUrl = URL.createObjectURL(blob);
        if (repostImage) {
          repostImage.src = currentObjectUrl;
          repostImage.style.opacity = "1";
        }
        if (repostLoading) repostLoading.hidden = true;
      })
      .catch(function () {
        if (repostLoading) repostLoading.hidden = true;
        toast(isRw() ? "Ntibyakunze gutegura ifoto" : "Could not generate the image");
      });
  }

  if (createRepostBtn) {
    createRepostBtn.addEventListener("click", function () {
      setRepostLang(currentLang, "#repostDialog");
      shareDialog.close();
      repostDialog.showModal();
      loadRepostImage();
    });
  }

  if (repostSaveBtn) {
    repostSaveBtn.addEventListener("click", function () {
      if (!currentBlob) return;
      var a = document.createElement("a");
      a.href = currentObjectUrl;
      a.download = "ytr-devotion-" + currentLang + ".png";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast(isRw() ? "Ifoto yabitswe" : "Image saved");
    });
  }

  if (repostShareBtn) {
    repostShareBtn.addEventListener("click", function () {
      if (!currentBlob) return;
      var file = new File([currentBlob], "ytr-devotion-" + currentLang + ".png", { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({
          files: [file],
          title: DATA.text[currentLang] || DATA.text.en,
          text: DATA.text[currentLang] || DATA.text.en,
        }).catch(function () {});
      } else if (repostSaveBtn) {
        repostSaveBtn.click();
      }
    });
  }
})();
