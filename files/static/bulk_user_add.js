var current_row = 0;

function validateName(name) {
  if (name) {
    return true;
  }
  else {
    return "Name cannot be blank";
  }
}

function validateEmail(email) {
  // Add regex
  if (!email) {
    return "Email cannot be blank";
  }
  return true;
}

function validateTeam(team, role) {
  // Check against list
  // No team is valid as planning are not on a team 
  if (team === "---" | !team) {
    if (role !== "Planning" & role !== "Guest" & role !== "SOOPP" & role !== "Alumni") {
      return "No team selected";
    }
  }
  return true;
}

function validateRole(role) {
  // Check against list
  if (role == "---") {
    return "Must select a role.";
  }
  return true;
}

function addUserRowButtonPress(row_id, disable_invalid_alert) {
  let nameInput = document.querySelector("." + row_id + ".name_input");
  let emailInput = document.querySelector("." + row_id + ".email_input");
  let selectTeam = document.querySelector("." + row_id + ".team_selection");
  let selectRole = document.querySelector("." + row_id + ".role_selection");
  let selectProgram = document.querySelector("." + row_id + ".program_selection");
  let sizeInput = document.querySelector("." + row_id + ".size_input")
  let button = document.querySelector("button." + row_id);

  const name = nameInput.value;
  const email = emailInput.value;
  let team = selectTeam.value;
  const role = selectRole.value;
  let program = selectProgram.value;
  const size = sizeInput.value

  vName = validateName(name);
  vEmail = validateEmail(email);
  vTeam = validateTeam(team, role);
  vRole = validateRole(role);

  let failedValidation = false;
  let error_message = "Invalid Entry:\n";

  if (vName !== true) {
    nameInput.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vName + "\n"
  }

  if (vEmail !== true) {
    emailInput.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vEmail + "\n";
  }

  if (vTeam !== true) {
    selectTeam.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vTeam + "\n";
  }

  if (vRole !== true) {
    selectRole.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vRole + "\n";
  }

  if (failedValidation) {
    if (!disable_invalid_alert) {
      alert(error_message)
    }
  }
  else {

    // alert("Trying to add:\nName: " + name + "\nEmail: " + email + "\nTeam: " + team + "\nRole: " + role);

    // if no team selected and it is valid, then set team to null 
    if (team === "---") {
      team = null;
    }

    if (program === "---") {
      program = null;
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
        "command": "add_user",
        "name": name,
        "email": email,
        "team": team,
        "role": role,
        "program": program,
        "size": size
      })
    })
      .then(res => {
        if (res.ok) {
          res.json().then(data => {
            const user_id = data["user_id"];
            const username = data["username"];
            console.log("Added User.\n    user id : " + user_id + "\n    username: " + username);
          })

          for (let field of [nameInput, emailInput, selectTeam, selectRole, selectProgram]) {
            field.disabled = true;
            field.style.backgroundColor = "grey";
          }

          button.style.backgroundColor = "green";
          button.disabled = true;
          button.textContent = "Added";
        }
        else {
          res.text().then(data => {
            console.log("Error: " + data);
            alert("Failed to add user. " + data);
          })
        }
      })
  }
}


function addUserRow(name, email, team, role, program, size) {

  const table = document.getElementById("new-user-table");

  current_row++;
  const row_id = "rowID" + current_row;

  let row = table.insertRow(1);
  row.setAttribute("class", row_id);

  let nameCell = row.insertCell(0);
  let nameInput = document.createElement("input");
  nameInput.setAttribute("type", "text");
  nameInput.setAttribute("class", row_id + " name_input")
  if (name) {
    nameInput.value = name;
  }
  nameCell.appendChild(nameInput);

  let emailCell = row.insertCell(1);
  let emailInput = document.createElement("input");
  emailInput.setAttribute("type", "email");
  emailInput.setAttribute("class", row_id + " email_input")
  if (email) {
    emailInput.value = email;
  }
  emailCell.appendChild(emailInput);


  let teamCell = row.insertCell(2);
  let selectTeam = document.createElement("select");
  let blank_team_opt = document.createElement("option");
  blank_team_opt.innerHTML = "---";
  selectTeam.appendChild(blank_team_opt);
  for (const team of teams) {
    let opt = document.createElement("option");
    opt.innerHTML = team;
    selectTeam.appendChild(opt);
  }
  selectTeam.setAttribute("class", row_id + " team_selection")
  if (team) {
    selectTeam.value = team;
  }
  teamCell.appendChild(selectTeam);

  let roleCell = row.insertCell(3);
  let selectRole = document.createElement("select");
  let blank_role_opt = document.createElement("option");
  blank_role_opt.innerHTML = "---";
  selectRole.appendChild(blank_role_opt);
  for (const role of roles) {
    let opt = document.createElement("option");
    opt.innerHTML = role;
    selectRole.appendChild(opt);
  }
  selectRole.setAttribute("class", row_id + " role_selection")
  if (role) {
    selectRole.value = role;
  }
  roleCell.appendChild(selectRole);

  let programCell = row.insertCell(4);
  let selectProgram = document.createElement("select");
  let noneOption = document.createElement("option");
  noneOption.innerHTML = "---";
  selectProgram.appendChild(noneOption);
  for (const pro of programs) {
    let opt = document.createElement("option");
    opt.innerHTML = pro;
    selectProgram.appendChild(opt);
  }
  selectProgram.setAttribute("class", row_id + " program_selection");
  if (program) {
    selectProgram.value = program;
  }
  programCell.appendChild(selectProgram);

  let sizeCell = row.insertCell(5);
  let sizeInput = document.createElement("input");
  sizeInput.setAttribute("type", "text");
  sizeInput.setAttribute("class", row_id + " size_input")
  if (size) {
    sizeInput.value = size;
  }
  sizeCell.appendChild(sizeInput);

  let submitButton = document.createElement("button");
  submitButton.innerText = "ADD";
  submitButton.setAttribute("onclick", "addUserRowButtonPress('" + row_id + "')")
  submitButton.setAttribute("class", row_id + " submit_button")
  let submitCell = row.insertCell(6);
  submitCell.appendChild(submitButton);
};

function handleCSVFile(file) {
  function checkFirstLine(line) {
    let headings = line.split(",");
    for (let i = 0; i < headings.length; i++) {
      headings[i] = headings[i].trim().toLowerCase();
    }
    if (headings[0] != "name" | headings[1] != "email" | headings[2] != "team" | headings[3] != "role" | headings[4] != "program" | headings[5] != "shirt size") {
      return false;
    }
    return true;
  }

  function handleCSVLine(line) {
    if (!line) {
      // If line is blank, ignore and treat as properly handled
      return true;
    }

    let values = line.split(",");

    for (let i = 0; i < values.length; i++) {
      values[i] = values[i].trim();
    }

    const name = values[0];
    const email = values[1];
    const team = values[2];
    const role = values[3];
    const program = values[4];
    const size = values[5];

    addUserRow(name, email, team, role, program, size);

  }

  let reader = new FileReader();
  reader.onload = function (event) {
    let lines = event.target.result.split("\n");

    // Check if the file is valid
    if (!checkFirstLine(lines[0])) {
      alert("Bad CSV Headings. Should be name,email,team,role");
    }
    else {
      // File headers are good
      for (line of lines.slice(1)) {
        handleCSVLine(line);
      }
    }
  }
  reader.readAsText(file);
};


function addAllUserButtonPress() {
  for (let row = 1; row <= current_row; row++) {
    let row_id = "rowID" + row;
    let button = document.querySelector("button." + row_id);
    if (!button.disabled) {
      addUserRowButtonPress(row_id, true);
    }
  }
}
