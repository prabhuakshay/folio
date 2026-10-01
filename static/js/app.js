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

// A form with `data-confirm` asks first in the confirmation sheet
// (templates/ui/confirm.html): removing a way to sign in can't be undone.
const sheet = document.getElementById("confirm");

document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!sheet || !form.dataset.confirm) return;
  event.preventDefault();
  sheet.querySelector("#confirm-question").textContent = form.dataset.confirm;
  sheet.querySelector("[data-confirm-detail]").textContent =
    form.dataset.confirmDetail ?? "";
  sheet.querySelector("[data-confirm-action]").textContent =
    form.dataset.confirmAction ?? "Continue";
  sheet.returnValue = "";
  sheet.addEventListener(
    "close",
    () => {
      // submit() skips the submit event, so this doesn't ask again.
      if (sheet.returnValue === "confirm") form.submit();
    },
    { once: true },
  );
  sheet.showModal();
});

// A `data-sheet` button opens the sheet it names. A tap on the dimmed page
// around any sheet closes it.
document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-sheet]");
  if (opener) document.getElementById(opener.dataset.sheet).showModal();
  if (event.target.matches("dialog.sheet")) event.target.close();
});

// A sheet the server sent back with `data-open`, such as one whose form was
// refused, opens as the page loads.
document.querySelector("dialog.sheet[data-open]")?.showModal();

// A sheet htmx fills (hx-target a dialog.sheet) opens once its content lands.
document.addEventListener("htmx:afterSwap", (event) => {
  const sheet = event.detail.target;
  if (sheet.matches("dialog.sheet") && !sheet.open) sheet.showModal();
});
