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
  let allergiesInput = document.querySelector("." + row_id + ".allergies")
  let raftingInput = document.querySelector("." + row_id + ".rafting")
  let hardhatInput = document.querySelector("." + row_id + ".hardhat")
  let sweaterInput = document.querySelector("." + row_id + ".sweater")
  let button = document.querySelector("button." + row_id);

  const name = nameInput.value;
  const email = emailInput.value;
  let team = selectTeam.value;
  const role = selectRole.value;
  let program = selectProgram.value;
  const size = sizeInput.value
  const rafting = raftingInput.value;
  const hardhat = hardhatInput.value;
  const allergies = allergiesInput.value;
  const sweater = sweaterInput.value;

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
        "size": size,
        "allergies": allergies,
        "hardhat": hardhat,
        "rafting": rafting,
        "sweater": sweater,
      })
    })
      .then(res => {
        if (res.ok) {
          res.json().then(data => {
            const user_id = data["user_id"];
            const username = data["username"];
            console.log("Added User.\n    user id : " + user_id + "\n    username: " + username);
          })

          for (let field of [nameInput, emailInput, selectTeam, selectRole, selectProgram, sizeInput]) {
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


function addUserRow(name, email, team, role, program, size, allergies, rafting, hardhat, sweater) {

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

  let allCell = row.insertCell(6);
  let allInput = document.createElement("input");
  allInput.setAttribute("type", "text");
  allInput.setAttribute("class", row_id + " allergies")
  if (allergies) {
    allInput.value = allergies;
  }
  allCell.appendChild(allInput);

  let raftCell = row.insertCell(7);
  let raftInput = document.createElement("input");
  raftInput.setAttribute("type", "text");
  raftInput.setAttribute("class", row_id + " rafting")
  if (rafting) {
    raftInput.value = rafting;
  }
  raftCell.appendChild(raftInput);

  let hardCell = row.insertCell(8);
  let hardInput = document.createElement("input");
  hardInput.setAttribute("type", "text");
  hardInput.setAttribute("class", row_id + " hardhat")
  if (hardhat) {
    hardInput.value = hardhat;
  }
  hardCell.appendChild(hardInput);

  let sweatCell = row.insertCell(9);
  let sweatInput = document.createElement("input");
  sweatInput.setAttribute("type", "text");
  sweatInput.setAttribute("class", row_id + " sweater")
  if (sweater) {
    sweatInput.value = sweater;
  }
  sweatCell.appendChild(sweatInput);

  let submitButton = document.createElement("button");
  submitButton.innerText = "ADD";
  submitButton.setAttribute("onclick", "addUserRowButtonPress('" + row_id + "')")
  submitButton.setAttribute("class", row_id + " submit_button")
  let submitCell = row.insertCell(10);
  submitCell.appendChild(submitButton);
};

function handleCSVFile(file) {
  function checkFirstLine(line) {
    let headings = line.split(",");
    for (let i = 0; i < headings.length; i++) {
      headings[i] = headings[i].trim().toLowerCase();
    }
    console.log(headings)
    if (headings[0] != "name" | headings[1] != "email" | headings[2] != "team" | headings[3] != "role" | headings[4] != "program" | headings[5] != "shirt size") {
      if (headings[0] != "first name" | headings[1] != "last name" | headings[2] != "email" | headings[3] != "team" | headings[4] != "role" | headings[5] != "program" | headings[6] != "shirt size") {
        return 0;
      }
      return 2;
    }
    return 1;
  }

  function handleCSVLine(line, split_name) {
    if (!line) {
      // If line is blank, ignore and treat as properly handled
      return true;
    }

    let values = line.split(",");

    for (let i = 0; i < values.length; i++) {
      values[i] = values[i].trim();
    }
    index = 0
    var name = values[index++];
    if (split_name){
        name += " " + values[index++];
    }
    const email = values[index++];
    const team = values[index++];
    const role = values[index++];
    const program = values[index++];
    const size = values[index++];
    const allergies = values[index++];
    const rafting = values[index++];
    const hardhat = values[index++];
    const sweater = values[index++];

    addUserRow(name, email, team, role, program, size, allergies, rafting, hardhat, sweater);

  }

  let reader = new FileReader();
  reader.onload = function (event) {
    let lines = event.target.result.split("\n");

    // Check if the file is valid
    heading = checkFirstLine(lines[0])
    if (heading == 0) {
      alert("Bad CSV Headings. Should be name,email,team,role,program,shirt size");
    }
    else {
      // File headers are good
      for (line of lines.slice(1)) {
        handleCSVLine(line, heading == 2);
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
