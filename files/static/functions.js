
HEX_COLOR_PATTERN = /^#?[0-9A-F]{6}$/i;

function postToServer(CSRFToken, toJSONBody) {
  return fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": CSRFToken,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(toJSONBody)
  })
}
