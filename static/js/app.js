// Switching tabs replaces the history entry, so Back stays inside a tab instead
// of walking through every tab visited. A stacked screen's back arrow goes back
// only when the page before was a Folio screen (not, say, the sign-in form it
// redirected through), and to its parent screen otherwise.
const previousScreen = sessionStorage.getItem("folio:screen");
if (document.querySelector("[data-tab-link]")) {
  sessionStorage.setItem("folio:screen", location.href);
}

document.addEventListener("click", (event) => {
  if (event.defaultPrevented || event.button !== 0) return;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

  const tab = event.target.closest("a[data-tab-link]");
  if (tab) {
    event.preventDefault();
    location.replace(tab.href);
    return;
  }

  const back = event.target.closest("a[data-back]");
  if (back && previousScreen && document.referrer === previousScreen) {
    event.preventDefault();
    history.back();
  }
});
