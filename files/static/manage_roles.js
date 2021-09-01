
function addRole(roleType) {
  if (!roleType) {
    return null;
  }

  let roleName = prompt("Enter the name of the new role:");
  let confirmed = confirm("Add role with name: " + roleName + " ?");
  if (!confirmed) {
    return null;
  }

  fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": csrf_token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      "command": "add_role",
      "role_name": roleName,
      "role_type": roleType,
      "role_color": null
    })
  })
    .then(res => {
      if (res.ok) {
        // Handle Success
        location.reload();
      }
      else {
        res.text().then(data => {
          console.error("Error: " + data);
          alert("Failed to add role.")
        })
      }
    })
}

function addEngFroshRoleButtonPress() {
  addRole("engfrosh_role");
}

function addProgramRoleButtonPress() {
  addRole("program_role");
}
