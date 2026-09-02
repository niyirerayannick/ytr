(function () {
  "use strict";

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  function isSecureContext() {
    return location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.hostname === "10.0.2.2" || location.hostname === "::1";
  }

  function isLocalDevelopmentHost() {
    return ["localhost", "127.0.0.1", "::1", "10.0.2.2"].indexOf(location.hostname) !== -1;
  }

  /* ---------- SERVICE WORKER REGISTRATION + UPDATES ---------- */
  var waitingWorker = null;
  var updateRequested = false;
  var reloadedForUpdate = false;
  var updateBanner = document.getElementById("pwaUpdate");
  var updateButton = document.getElementById("pwaUpdateButton");

  function showUpdateBanner(worker) {
    waitingWorker = worker;
    if (updateBanner) updateBanner.hidden = false;
  }

  if ("serviceWorker" in navigator && isSecureContext() && !isLocalDevelopmentHost()) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/service-worker.js").then(function (registration) {
        if (registration.waiting && navigator.serviceWorker.controller) {
          showUpdateBanner(registration.waiting);
        }
        registration.addEventListener("updatefound", function () {
          var newWorker = registration.installing;
          if (!newWorker) return;
          newWorker.addEventListener("statechange", function () {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              showUpdateBanner(newWorker);
            }
          });
        });
      }).catch(function () {
        /* Offline support degrades to normal online browsing. */
      });

      // clients.claim() in the worker's activate handler also fires
      // controllerchange the very first time a page becomes controlled —
      // not just on a genuine update. Reloading then would mean every first
      // visit reloads itself once. Only reload when *we* requested the skip
      // (see the Update button handler below).
      navigator.serviceWorker.addEventListener("controllerchange", function () {
        if (!updateRequested || reloadedForUpdate) return;
        reloadedForUpdate = true;
        window.location.reload();
      });
    });
  }

  if (updateButton) {
    updateButton.addEventListener("click", function () {
      if (waitingWorker) {
        updateRequested = true;
        waitingWorker.postMessage({ type: "SKIP_WAITING" });
      }
      if (updateBanner) updateBanner.hidden = true;
    });
  }

  /* ---------- INSTALL PROMPT (Chromium) ---------- */
  var deferredPrompt = null;
  var installCard = document.getElementById("pwaInstallCard");
  var installButton = document.getElementById("pwaInstallButton");
  var installDismiss = document.getElementById("pwaInstallDismiss");
  var DISMISS_DAYS = 14;

  function dismissedRecently(key) {
    try {
      var at = localStorage.getItem(key);
      return !!at && Date.now() - parseInt(at, 10) < DISMISS_DAYS * 24 * 60 * 60 * 1000;
    } catch (e) {
      return false;
    }
  }

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferredPrompt = event;
    if (installCard && !isStandalone() && !dismissedRecently("ytr_pwa_install_dismissed")) {
      installCard.hidden = false;
    }
  });

  if (installButton) {
    installButton.addEventListener("click", function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () {
        deferredPrompt = null;
        if (installCard) installCard.hidden = true;
      });
    });
  }

  if (installDismiss) {
    installDismiss.addEventListener("click", function () {
      if (installCard) installCard.hidden = true;
      try {
        localStorage.setItem("ytr_pwa_install_dismissed", String(Date.now()));
      } catch (e) {}
    });
  }

  window.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    if (installCard) installCard.hidden = true;
    var iosCard = document.getElementById("pwaIosInstall");
    if (iosCard) iosCard.hidden = true;
  });

  /* ---------- iOS MANUAL INSTALL INSTRUCTIONS ---------- */
  var iosInstall = document.getElementById("pwaIosInstall");
  var iosDismiss = document.getElementById("pwaIosDismiss");

  function isIos() {
    return /iphone|ipad|ipod/i.test(window.navigator.userAgent) && !window.MSStream;
  }

  if (iosInstall && isIos() && !isStandalone() && !dismissedRecently("ytr_pwa_ios_dismissed")) {
    iosInstall.hidden = false;
  }

  if (iosDismiss) {
    iosDismiss.addEventListener("click", function () {
      if (iosInstall) iosInstall.hidden = true;
      try {
        localStorage.setItem("ytr_pwa_ios_dismissed", String(Date.now()));
      } catch (e) {}
    });
  }

  /* ---------- MEMBER BOTTOM NAV "MORE" DRAWER ---------- */
  var moreToggle = document.getElementById("pwaMoreToggle");
  var moreSheet = document.getElementById("pwaMoreSheet");
  var moreBackdrop = document.getElementById("pwaMoreBackdrop");

  function closeMoreSheet() {
    if (!moreSheet || moreSheet.hidden) return;
    moreSheet.hidden = true;
    if (moreBackdrop) moreBackdrop.hidden = true;
    if (moreToggle) moreToggle.setAttribute("aria-expanded", "false");
  }

  function openMoreSheet() {
    if (!moreSheet) return;
    moreSheet.hidden = false;
    if (moreBackdrop) moreBackdrop.hidden = false;
    if (moreToggle) moreToggle.setAttribute("aria-expanded", "true");
  }

  if (moreToggle && moreSheet) {
    moreToggle.addEventListener("click", function () {
      if (moreSheet.hidden) openMoreSheet(); else closeMoreSheet();
    });
    moreSheet.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMoreSheet);
    });
    var moreLogoutButton = moreSheet.querySelector("form button[type=submit]");
    if (moreLogoutButton) moreLogoutButton.addEventListener("click", closeMoreSheet);
  }
  if (moreBackdrop) moreBackdrop.addEventListener("click", closeMoreSheet);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeMoreSheet();
  });

  /* ---------- ONLINE / OFFLINE INDICATOR ---------- */
  var networkStatus = document.getElementById("pwaNetworkStatus");
  var networkStatusTimer;

  function showNetworkStatus(message, autoHide) {
    if (!networkStatus) return;
    networkStatus.textContent = message;
    networkStatus.hidden = false;
    clearTimeout(networkStatusTimer);
    if (autoHide) {
      networkStatusTimer = setTimeout(function () {
        networkStatus.hidden = true;
      }, 4000);
    }
  }

  window.addEventListener("offline", function () {
    showNetworkStatus("You're offline — showing available content.", false);
  });
  window.addEventListener("online", function () {
    showNetworkStatus("Back online.", true);
  });
})();
