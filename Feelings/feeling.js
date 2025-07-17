
function submitEmotion() {
    const input = document.getElementById('emotionInput');
    const text = input.value.trim();

    if (text === '') {
        alert('Please write something before submitting.');
        return;
    }

    const entry = document.createElement('div');
    entry.className = 'entry';
    entry.textContent = text;

    const container = document.getElementById('entriesContainer');
    container.prepend(entry);
    input.value = '';
}
