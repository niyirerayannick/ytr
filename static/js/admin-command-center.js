document.addEventListener("alpine:init", () => {
  Alpine.data("commandPalette", () => ({
    show: false,
    query: "",
    _trigger: null,
    open() {
      this._trigger = document.activeElement;
      this.show = true;
      this.query = "";
      this.$nextTick(() => this.$refs.input && this.$refs.input.focus());
    },
    close() {
      this.show = false;
      if (this._trigger && this._trigger.focus) this._trigger.focus();
    },
  }));
});

document.addEventListener("keydown", (event) => {
  const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
  const modifier = isMac ? event.metaKey : event.ctrlKey;
  if (modifier && event.key.toLowerCase() === "k") {
    event.preventDefault();
    window.dispatchEvent(new CustomEvent("open-palette"));
  }
});
