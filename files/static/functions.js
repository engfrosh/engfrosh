
HEX_COLOR_PATTERN = /^#?[0-9A-F]{6}$/i;

function postToServerURL(CSRFToken, toJSONBody, url) {
  return fetch(url, {
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
function postToServer(CSRFToken, toJSONBody) {
    return postToServerURL(CSRFToken, toJSONBody, "");
}

