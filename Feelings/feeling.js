function submitEmotion() {
  const input = document.getElementById('emotionInput');
  const mood = document.getElementById('moodSelect').value;
  const text = input.value.trim();
  const time = new Date().toLocaleString();

  if (text === '') {
    alert('Please write something before submitting.');
    return;
  }

  const newEntry = {
    id: Date.now().toString(),
    text,
    mood,
    time,
    likes: 0
  };

  const entries = JSON.parse(localStorage.getItem('entries') || '[]');
  entries.unshift(newEntry);
  localStorage.setItem('entries', JSON.stringify(entries));

  input.value = '';
  updateCharCount();
  renderEntries();
}

function renderEntries() {
  const entries = JSON.parse(localStorage.getItem('entries') || '[]');
  const container = document.getElementById('entriesContainer');
  container.innerHTML = '';

  entries.forEach(entry => {
    const div = document.createElement('div');
    div.className = 'entry';
    div.innerHTML = `
      <strong>${entry.mood}</strong> ${entry.text}
      <br><small>${entry.time}</small>
      <br>
      <button onclick="likeEntry('${entry.id}')">❤️ ${entry.likes}</button>
    `;
    container.appendChild(div);
  });
}

function likeEntry(id) {
  const entries = JSON.parse(localStorage.getItem('entries') || '[]');
  const updated = entries.map(entry => {
    if (entry.id === id) entry.likes += 1;
    return entry;
  });
  localStorage.setItem('entries', JSON.stringify(updated));
  renderEntries();
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
}

function updateCharCount() {
  const len = document.getElementById('emotionInput').value.length;
  document.getElementById('charCount').textContent = `${len}/1000`;
}

document.addEventListener('DOMContentLoaded', () => {
  renderEntries();
  updateCharCount();
  document.getElementById('emotionInput').addEventListener('input', updateCharCount);
});
