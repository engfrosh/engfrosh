
function lockButtonPress(tagID) {
  postToServer(csrf_token, {
    "command": "lock_channel_group",
    "tag_id": tagID
  }).then(
    res => {
      if (res.ok) {
        alert("Locked Channel");
      }
      else {
        res.text().then(data => {
          alert("Failed to lock channel: " + data)
        })
      }
    }
  )
}

function unlockButtonPress(tagID) {
  postToServer(csrf_token, {
    "command": "unlock_channel_group",
    "tag_id": tagID
  }).then(
    res => {
      if (res.ok) {
        alert("Unlocked Channel");
      }
      else {
        res.text().then(data => {
          alert("Failed to unlock channel: " + data)
        })
      }
    }
  )
}
