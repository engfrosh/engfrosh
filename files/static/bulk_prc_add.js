var current_row = 0;
var heading_count = 0;

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

function getValue(inputs, maps, type){
    for (let i = 0; i < maps.length; i++){
        if (maps[i] == type){
            return inputs[i];
        }
    }
    return "";
}

function addPRCRowButtonPress(row_id, disable_invalid_alert) {
  var inputs = [];
  var maps = [];
  for (let i = 0; i < heading_count; i++){
    let input = document.querySelector("." + row_id + " .input" + i);
    let sel = document.querySelector("#select" + i);
    maps.push(sel.value);
    inputs.push(input.value);
  }
  var fname = getValue(inputs, maps, "fname");
  var lname = getValue(inputs, maps, "lname");
  var email = getValue(inputs, maps, "email");
  var prc = getValue(inputs, maps, "prc");
  var grade = getValue(inputs, maps, "grade");
  var contract = getValue(inputs, maps, "contract");
  var waiver = getValue(inputs, maps, "waiver");
  var training = getValue(inputs, maps, "training");
  var hardhat = getValue(inputs, maps, "hardhat");
  var hardhat_paid = getValue(inputs, maps, "hardhat_paid");
  var breakfast = getValue(inputs, maps, "breakfast");
  var breakfast_paid = getValue(inputs, maps, "breakfast_paid");
  var rafting = getValue(inputs, maps, "rafting");
  var rafting_paid = getValue(inputs, maps, "rafting_paid");
  var sweater_size = getValue(inputs, maps, "sweater_size");
  var shirt_size = getValue(inputs, maps, "shirt_size");
  var allergies = getValue(inputs, maps, "allergies");
  var shifts = getValue(inputs, maps, "shifts");

  let button = document.querySelector("button." + row_id);

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
        "prc": prc,
        "grade": grade,
        "contract": contract,
        "waiver": waiver,
        "training": training,
        "hardhat": hardhat,
        "hardhat_paid": hardhat_paid,
        "breakfast": breakfast,
        "breakfast_paid": breakfast_paid,
        "rafting": rafting,
        "rafting_paid": rafting_paid,
        "sweater_size": sweater_size,
        "shirt_size": shirt_size,
        "allergies": allergies,
        "shifts": shifts,
      })
    })
      .then(res => {
        if (res.ok) {
          res.json().then(data => {
            const user_id = data["user_id"];
            const username = data["username"];
            console.log("Added bulk data.\n    user id : " + user_id + "\n    username: " + username);
          })

          button.style.backgroundColor = "green";
          button.disabled = true;
          button.textContent = "Added";
        }
        else {
          res.text().then(data => {
            console.log("Error: " + data);
            alert("Failed to add bulk data. " + data);
          })
        }
      })
}
var options = ["None", "First Name", "Last Name", "Email", "PRC Issued", "Brightspace Grade", "Contract", "Waiver", "Training", "Hardhat", "Hardhat Paid", "Breakfast", "Breakfast Paid", "Rafting", "Rafting Paid", "Sweater Size", "Shirt Size", "Allergies", "Shifts"];
var map = ["none", "fname", "lname", "email", "prc", "grade", "contract", "waiver", "training", "hardhat", "hardhat_paid", "breakfast", "breakfast_paid", "rafting", "rafting_paid", "sweater_size", "shirt_size", "allergies", "shifts"];


function addHeadingRow(values) {
    heading_count = values.length;
    const table = document.getElementById("new-user-table");
    table.innerHTML = "";
    var thead = table.createTHead();
    var topHead = thead.insertRow(0);
    var bottomHead = thead.insertRow(1);
    for (let i = 0; i < values.length; i++){
        var tCell = topHead.insertCell(i);
        var sel = document.createElement("select");
        sel.id = "select" + i;
        tCell.appendChild(sel);
        for (let j = 0; j < options.length; j++){
            var option = document.createElement("option");
            option.value = map[j];
            option.text = options[j];
            sel.appendChild(option);
        }

        var bCell = bottomHead.insertCell(i);
        bCell.innerHTML = values[i];
    }
}

function addPRCRow(values) {
  if (heading_count == 0){
    addHeadingRow(["Email", "First Name", "Last Name", "Value 1", "Value 2", "Value 3", "Value 4"]);
  }
  const table = document.getElementById("new-user-table");

  current_row++;
  const row_id = "rowID" + current_row;

  let row = table.insertRow();
  row.setAttribute("class", row_id);
  let index = 0;
  if (values != null){
    for (let i = 0; i < values.length; i++){
      let cell = row.insertCell(i);
      let input = document.createElement("input");
      input.setAttribute("type", "text");
      input.setAttribute("class", row_id + " input" + i)
      input.value = values[i];
      cell.appendChild(input);
      index++;
    }
  }else{
    for (let i = 0; i < heading_count; i++){
      let cell = row.insertCell(i);
      let input = document.createElement("input");
      input.setAttribute("type", "text");
      input.setAttribute("class", row_id + " input" + i)
      cell.appendChild(input);
      index++
    }
  }

  let submitButton = document.createElement("button");
  submitButton.innerText = "ADD";
  submitButton.setAttribute("onclick", "addPRCRowButtonPress('" + row_id + "')")
  submitButton.setAttribute("class", row_id + " submit_button")
  let submitCell = row.insertCell(index);
  submitCell.appendChild(submitButton);
};

function handleCSVFile(file) {
  function handleCSVLine(line) {
    if (!line) {
      // If line is blank, ignore and treat as properly handled
      return true;
    }

    let values = line.split(",");

    for (let i = 0; i < values.length; i++) {
      values[i] = values[i].trim();
    }

    addPRCRow(values);

  }

  let reader = new FileReader();
  reader.onload = function (event) {
    let lines = event.target.result.split("\n");

    // Check if the file is valid
    let headings = lines[0].split(",");
    heading_count = headings.length;
    addHeadingRow(headings);
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
