(function () {
  "use strict";

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  function isSecureContext() {
    return location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1";
  }

  /* ---------- SERVICE WORKER REGISTRATION + UPDATES ---------- */
  var waitingWorker = null;
  var updateBanner = document.getElementById("pwaUpdate");
  var updateButton = document.getElementById("pwaUpdateButton");

  function showUpdateBanner(worker) {
    waitingWorker = worker;
    if (updateBanner) updateBanner.hidden = false;
  }

  if ("serviceWorker" in navigator && isSecureContext()) {
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

      var reloadedForUpdate = false;
      navigator.serviceWorker.addEventListener("controllerchange", function () {
        if (reloadedForUpdate) return;
        reloadedForUpdate = true;
        window.location.reload();
      });
    });
  }

  if (updateButton) {
    updateButton.addEventListener("click", function () {
      if (waitingWorker) waitingWorker.postMessage({ type: "SKIP_WAITING" });
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
