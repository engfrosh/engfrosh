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

function addPRCRowButtonPress(row_id, disable_invalid_alert) {
  let fnameInput = document.querySelector("." + row_id + ".first_name_input");
  let lnameInput = document.querySelector("." + row_id + ".last_name_input");
  let emailInput = document.querySelector("." + row_id + ".email_input");
  let issuedInput = document.querySelector("." + row_id + ".issued_input");
  let button = document.querySelector("button." + row_id);

  const fname = fnameInput.value;
  const lname = lnameInput.value;
  const email = emailInput.value;
  const issued = issuedInput.value;
  if(issued == ""){
    console.log(fname + " " + lname + " : " + email + " not issued yet!");
    button.style.backgroundColor = "red";
    button.disabled = true;
    button.textContent = "No PRC";
    return;
  }
  vFName = validateName(fname);
  vLName = validateName(lname);
  vEmail = validateEmail(email);

  let failedValidation = false;
  let error_message = "Invalid Entry:\n";

  if (vFName !== true) {
    fnameInput.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vFName + "\n"
  }
  if (vLName !== true) {
    lnameInput.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vLName + "\n"
  }

  if (vEmail !== true) {
    emailInput.style.backgroundColor = "red";
    failedValidation = true;
    error_message += "    " + vEmail + "\n";
  }
  else {

    // alert("Trying to add:\nName: " + name + "\nEmail: " + email + "\nTeam: " + team + "\nRole: " + role);

    fetch("", {
      method: "POST",
      mode: "cors",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "command": "add_prc",
        "first_name": fname,
        "email": email,
        "last_name": lname,
        "issued": issued,
      })
    })
      .then(res => {
        if (res.ok) {
          res.json().then(data => {
            const user_id = data["user_id"];
            const username = data["username"];
            console.log("Added PRC.\n    user id : " + user_id + "\n    username: " + username);
          })

          for (let field of [fnameInput, lnameInput, emailInput, issuedInput]) {
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


function addPRCRow(fname, lname, email, issued) {

  const table = document.getElementById("new-user-table");

  current_row++;
  const row_id = "rowID" + current_row;

  let row = table.insertRow(1);
  row.setAttribute("class", row_id);

  let fnameCell = row.insertCell(0);
  let fnameInput = document.createElement("input");
  fnameInput.setAttribute("type", "text");
  fnameInput.setAttribute("class", row_id + " first_name_input")
  if (fname) {
    fnameInput.value = fname;
  }
  fnameCell.appendChild(fnameInput);

  let lnameCell = row.insertCell(1);
  let lnameInput = document.createElement("input");
  lnameInput.setAttribute("type", "text");
  lnameInput.setAttribute("class", row_id + " last_name_input")
  if (lname) {
    lnameInput.value = lname;
  }
  lnameCell.appendChild(lnameInput);


  let emailCell = row.insertCell(2);
  let emailInput = document.createElement("input");
  emailInput.setAttribute("type", "email");
  emailInput.setAttribute("class", row_id + " email_input")
  if (email) {
    emailInput.value = email;
  }
  emailCell.appendChild(emailInput);

  let issuedCell = row.insertCell(3);
  let issuedInput = document.createElement("input");
  issuedInput.setAttribute("type", "text");
  issuedInput.setAttribute("class", row_id + " issued_input")
  if (issued) {
    issuedInput.value = issued;
  }
  issuedCell.appendChild(issuedInput);


  let submitButton = document.createElement("button");
  submitButton.innerText = "ADD";
  submitButton.setAttribute("onclick", "addPRCRowButtonPress('" + row_id + "')")
  submitButton.setAttribute("class", row_id + " submit_button")
  let submitCell = row.insertCell(4);
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

    const fname = values[0];
    const lname = values[1];
    const email = values[2];
    const issued = values[3];

    addPRCRow(fname, lname, email, issued);

  }

  let reader = new FileReader();
  reader.onload = function (event) {
    let lines = event.target.result.split("\n");

    // Check if the file is valid
    // File headers are good
    for (line of lines.slice(1)) {
      handleCSVLine(line);
    }
  }
  reader.readAsText(file);
};


function addAllPRCButtonPress() {
  for (let row = 1; row <= current_row; row++) {
    let row_id = "rowID" + row;
    let button = document.querySelector("button." + row_id);
    if (!button.disabled) {
      addPRCRowButtonPress(row_id, true);
    }
  }
}
