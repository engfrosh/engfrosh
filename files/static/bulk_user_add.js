var current_row = 0;

function addUserRowButtonPress(row_id) {
    let nameInput = document.querySelector("." + row_id + ".name_input");
    let emailInput = document.querySelector("." + row_id + ".email_input");
    let selectTeam = document.querySelector("." + row_id + ".team_selection");
    let selectRole = document.querySelector("." + row_id + ".role_selection");
    let button = document.querySelector("button." + row_id);
    
    const name = nameInput.value;
    const email = emailInput.value;
    const team = selectTeam.value;
    const role = selectRole.value; 

    // Validate input here 

    nameInput.disabled = true;
    emailInput.disabled = true;
    selectTeam.disabled = true;
    selectRole.disabled = true;

    button.style.backgroundColor = "Orange";
    button.disabled = true;
    button.textContent = "Added";
    
    alert("Button " + row_id + "\nName: " + name + "\nEmail: " + email + "\nTeam: " + team + "\nRole: " + role);
}

function addUserRow() {

    const table = document.getElementById("new-user-table");

    const optionInfo = document.getElementById("option-info");

    current_row++;
    const row_id = "rowID" + current_row;

    let row = table.insertRow(1);
    row.setAttribute("class", row_id);

    let nameCell = row.insertCell(0);
    let nameInput = document.createElement("input");
    nameInput.setAttribute("type", "text");
    nameInput.setAttribute("class", row_id + " name_input")
    nameCell.appendChild(nameInput);

    let emailCell = row.insertCell(1);
    let emailInput = document.createElement("input");
    emailInput.setAttribute("type", "email");
    emailInput.setAttribute("class", row_id + " email_input")
    emailCell.appendChild(emailInput);

    let teamCell = row.insertCell(2);
    let selectTeam = document.createElement("select");
    for (const team of teams) {
        let opt = document.createElement("option");
        opt.innerHTML = team;
        selectTeam.appendChild(opt);
    }
    selectTeam.setAttribute("class", row_id + " team_selection")
    teamCell.appendChild(selectTeam);

    let roleCell = row.insertCell(3);
    let selectRole = document.createElement("select");
    for (const role of roles) {
        let opt = document.createElement("option");
        opt.innerHTML = role;
        selectRole.appendChild(opt);
    }
    selectRole.setAttribute("class", row_id + " role_selection")
    roleCell.appendChild(selectRole);


    let submitButton = document.createElement("button");
    submitButton.innerText = "ADD";
    submitButton.setAttribute("onclick", "addUserRowButtonPress('" + row_id + "')")
    submitButton.setAttribute("class", row_id + " submit_button")
    let submitCell = row.insertCell(4);
    submitCell.appendChild(submitButton);
}
