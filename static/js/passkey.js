// A `data-passkey` button runs a passkey ceremony against the server's JSON
// views: "register" adds one and goes to `data-next`; "sign-in" uses one and
// goes where the server says. The browser's own JSON helpers translate the
// server's options and the authenticator's answer.
const csrfToken = () =>
  document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)?.[1] ?? "";

async function post(url, body = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail);
  return data;
}

async function register(button) {
  const options = await post(button.dataset.begin);
  const credential = await navigator.credentials.create({
    publicKey: PublicKeyCredential.parseCreationOptionsFromJSON(options),
  });
  await post(button.dataset.complete, credential.toJSON());
  return button.dataset.next;
}

async function signIn(button) {
  const options = await post(button.dataset.begin);
  const credential = await navigator.credentials.get({
    publicKey: PublicKeyCredential.parseRequestOptionsFromJSON(options),
  });
  const result = await post(button.dataset.complete, credential.toJSON());
  return result.redirect_url;
}

for (const button of document.querySelectorAll("[data-passkey]")) {
  const status = document.getElementById(button.getAttribute("aria-describedby"));
  if (!window.PublicKeyCredential?.parseCreationOptionsFromJSON) {
    button.disabled = true;
    status.textContent = "This browser can't use passkeys.";
    continue;
  }
  button.addEventListener("click", async () => {
    button.disabled = true;
    status.textContent = "";
    try {
      const ceremony = button.dataset.passkey === "register" ? register : signIn;
      location.assign(await ceremony(button));
    } catch (error) {
      button.disabled = false;
      status.textContent =
        error.name === "NotAllowedError"
          ? "Cancelled. Try again when you're ready."
          : error.message || "That didn't work. Try again.";
    }
  });
}
