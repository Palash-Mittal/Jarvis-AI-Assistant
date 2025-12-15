console.log("Renderer loaded");

// Check if preload exposed jarvis:
if (!window.jarvis) {
  console.error("ERROR: window.jarvis is undefined (preload not loaded)");
}

document.getElementById("sendBtn").onclick = () => {
  const text = document.getElementById("userInput").value;
  if (!text.trim()) return;

  addMessage(text, "user");

  if (window.jarvis) {
    window.jarvis.send(text);
  } else {
    console.error("Cannot send — jarvis API missing!");
  }
};

if (window.jarvis) {
  window.jarvis.onResponse((data) => {
    try {
      const obj = JSON.parse(data);
      addMessage(obj.reply, "jarvis");
    } catch {
      addMessage(data, "jarvis");
    }
  });
}

function addMessage(text, sender) {
  const msgBox = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "message " + sender;
  div.textContent = `${sender === "user" ? "YOU" : "JARVIS"}: ${text}`;
  msgBox.appendChild(div);
  msgBox.scrollTop = msgBox.scrollHeight;
}
