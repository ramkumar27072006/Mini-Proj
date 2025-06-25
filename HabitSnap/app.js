
const form = document.getElementById('habit-form');
const input = document.getElementById('habit-input');
const photoInput = document.getElementById('habit-photo');
const sectionContainer = document.getElementById('month-sections');

let habits = JSON.parse(localStorage.getItem('habits') || '[]');

function groupByMonth(entries) {
  return entries.reduce((acc, entry) => {
    const date = new Date(entry.date);
    const key = `${date.toLocaleString('default', { month: 'long' })} ${date.getFullYear()}`;
    acc[key] = acc[key] || [];
    acc[key].push(entry);
    return acc;
  }, {});
}

function render() {
  sectionContainer.innerHTML = '';
  const grouped = groupByMonth(habits);
  for (const [month, entries] of Object.entries(grouped)) {
    const section = document.createElement('details');
    section.innerHTML = `<summary><strong>${month}</strong></summary>`;
    entries.forEach((entry, index) => {
      const item = document.createElement('div');
      item.className = 'entry';
      item.innerHTML = `
        <p>${new Date(entry.date).toLocaleDateString()} - ${entry.text}</p>
        <img src="${entry.photo}" alt="proof" width="100" />
        <button onclick="deleteEntry('${entry.date}')">❌ Delete</button>
      `;
      section.appendChild(item);
    });
    sectionContainer.appendChild(section);
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const file = photoInput.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(event) {
    const entry = {
      text: input.value,
      date: new Date().toISOString(),
      photo: event.target.result
    };
    habits.push(entry);
    localStorage.setItem('habits', JSON.stringify(habits));
    input.value = '';
    photoInput.value = '';
    render();
  };
  reader.readAsDataURL(file);
});

function deleteEntry(date) {
  habits = habits.filter(entry => entry.date !== date);
  localStorage.setItem('habits', JSON.stringify(habits));
  render();
}

render();
