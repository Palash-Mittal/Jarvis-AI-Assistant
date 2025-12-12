document.getElementById("sendBtn").onclick = () => {
  const input = document.getElementById("userInput").value;
  window.jarvis.send(input);
};

window.jarvis.onResponse((data) => {
  console.log("JARVIS SAID:", data);
  document.getElementById("output").innerText = data;
});
