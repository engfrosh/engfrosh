function setupNewServerButtonPress() {
  let serverNamePrompt = "Enter the name of the new server:";
  let serverName = "";
  do {
    serverName = prompt(serverNamePrompt);
    console.log("Got server name: " + serverName);
    if (serverName === null) {
      console.log("Create server cancelled.");
      return;
    }
    serverNamePrompt = "Invalid server name. The server name must be between 2 and 100 characters.";
  } while (!serverName || serverName.length < 2 || serverNamePrompt.length > 100);
  postToServer(csrf_token, {
    "command": "create_new_guild",
    "name": serverName
  }).then(
    res => {
      if (res.ok) {
        res.json().then(data => {
          alert("Guild created with name: " + data["guild"]["name"] + " and id: " + data["guild"]["id"] + "\n\nReloading...");
          location.reload();
        })
      }
      else {
        res.text().then(data => {
          alert("Failed to create guild: " + data);
        })
      }
    }
  )
}

function scanForServersButtonPress() {
  postToServer(csrf_token, {
    "command": "scan_for_guilds"
  }).then(
    res => {
      if (res.ok) {
        res.json().then(data => {
          if (data["scan_results"]["num_added"] || data["scan_results"]["num_existing_updated"] || data["scan_results"]["num_removed"]) {
            alert("Scanning complete, changes found, reloading now...");
            location.reload();
          } else {
            alert("Scanning complete, no changes found.");
          }
        });
      }
      else {
        res.text().then(data => {
          alert("Failed to scan for guilds: " + data)
        });
      }
    }
  )
}

function get1UseInviteButtonPress(serverId) {
  postToServer(csrf_token, {
    "command": "get_one_use_invite",
    "guild_id": serverId
  }).then(
    res => {
      if (res.ok) {
        res.json().then(data => {
          navigator.clipboard.writeText(data["invite"]["full_url"]).then(
            copied_data => {
              alert("Copied invite to clipboard: " + data["invite"]["full_url"]);
            }
          );
        });
      } else {
        res.text().then(data => {
          alert("Failed to get invite: " + data);
        });
      }
    }
  );
}
