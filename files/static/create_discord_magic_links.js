function buttonCopyGenerator(text, button) {
  return function () {
    navigator.clipboard.writeText(text)
      .then(data => {
        button.textContent = "Copied";
        button.style.backgroundColor = "White";
      });
  };
};

function get_magic_link(user_id) {
  fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      'X-CSRFToken': csrf_token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ "command": "return_link", "user_id": user_id })
  })
    .then(res => {
      if (res.ok) {
        res.json().then(data => {
          const cls = "user_" + user_id;
          const button = document.querySelector("td.create_link." + cls + " button");
          button.style.backgroundColor = "green";
          button.textContent = "Copy Link";
          button.onclick = buttonCopyGenerator(data["link"], button);
          let email_button = document.querySelector("td.email_link." + cls + " button");
          email_button.disabled = true;
        })
      }
      else {
        alert("Bad response " + res.status + " Could not get link.")

      }
    });
};

function email_magic_link(user_id) {
  fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      'X-CSRFToken': csrf_token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ "command": "send_link_email", "user_id": user_id })
  })
    .then(res => {
      console.log(res);
      if (res.ok) {
        res.json().then(data => {
          const cls = "user_" + user_id;
          let button = document.querySelector("td.email_link." + cls + " button");
          button.style.backgroundColor = "green";
          button.textContent = "Email Sent!";
          button.disabled = true;
          let link_button = document.querySelector("td.create_link." + cls + " button");
          link_button.disabled = true;
        })
      }
      else {
        alert("Bad response " + res.status + " Could not email user.")

      }
    });
};

function add10Button() {
  let count = 0;

  let cur_ids;
  if (user_ids.length > 10) {
    cur_ids = user_ids.slice(0, 10);
    user_ids = user_ids.slice(10);
  }
  else {
    cur_ids = user_ids;
    user_ids = [];
  }

  for (id of cur_ids) {
    console.log("Adding user " + id);
    email_magic_link(id);

    count += 1;
    if (count >= 10) {
      return;
    }
  }
}
