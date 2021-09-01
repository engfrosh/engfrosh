
let newRowID = 1;

function addDiscordRoleButton(team_id) {
  fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      'X-CSRFToken': csrf_token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ "command": "add_discord_role", "team_id": team_id })
  })
    .then(res => {
      console.log(res);
      if (res.ok) {
        let cell = document.querySelector("td.discord_role.team" + team_id);
        cell.innerHTML = "✔";
      }
      else {
        alert("Bad response " + res.status)

      }
    });
};

function addTeam(teamName) {
  if (!teamName) {
    alert("Team name cannot be empty");
    return null;
  }
  let confirmed = confirm("Add team with name: " + teamName + " ?");
  if (confirmed) {
    fetch("", {
      method: "POST",
      mode: "cors",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "command": "add_team",
        "team_name": teamName,
        "team_color": null
      })
    })
      .then(res => {
        if (res.ok) {
          res.json().then(data => {
            const team_id = data["team_id"];
            const team_name = data["team_name"];
            console.log("Added Team.\n    team id : " + team_id + "\n    team name: " + team_name);
          })

          location.reload();

        }
        else {
          res.text().then(data => {
            console.log("Error: " + data);
            alert("Failed to add team. " + data);
          })
        }
      })
  }

};


function addTeamButtonPress() {
  const teamName = prompt("Enter the team name:");
  addTeam(teamName);
};

function updateTeam(teamID, colorNumber) {
  fetch("", {
    method: "POST",
    mode: "cors",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": csrf_token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      "command": "update_team",
      "team_id": teamID,
      "team_color": colorNumber
    })
  })
    .then(res => {
      if (res.ok) {
        res.json().then(data => {
          console.log(data);
          const teamID = data["team_id"];
          const teamName = data["team_name"];
          const colorCode = data["color_code"];

          // Only updates color currently
          if (colorCode !== null) {
            let colorCell = document.querySelector(".color_box.team" + teamID);
            colorCell.innerHTML = "";
            colorCell.setAttribute("style", "background-color:" + colorCode + ";");
          }
        })
      }
      else {
        res.text().then(data => {
          console.log("Error: " + data);
          alert("Failed to add team. " + data);
        })
      }
    })

}

function addColorButtonPress(teamID) {
  const colorCandidate = prompt("Enter the hex code of the color:");

  if (!HEX_COLOR_PATTERN.test(colorCandidate)) {
    alert(colorCandidate + " is not a valid hex color code.");
    return null;
  }

  const colorNumber = parseInt(colorCandidate.replace(/^#/, ""), 16);

  updateTeam(teamID, colorNumber);
}
