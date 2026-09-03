const form = document.getElementById('contact-form');
const firstNameInput = document.getElementById('firstName');
const lastNameInput = document.getElementById('lastName');
const list = document.getElementById('contact-list');
const errorEl = document.getElementById('error');

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function clearError() {
  errorEl.hidden = true;
}

function renderContacts(contacts) {
  list.innerHTML = '';
  if (contacts.length === 0) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = 'No contacts yet.';
    list.appendChild(empty);
    return;
  }
  contacts.forEach((contact) => {
    const li = document.createElement('li');

    const info = document.createElement('span');
    info.className = 'contact-info';
    info.innerHTML =
      '<svg class="contact-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
      '<path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>' +
      '</svg>';

    const name = document.createElement('span');
    name.textContent = `${contact.firstName} ${contact.lastName}`;
    info.appendChild(name);

    const removeBtn = document.createElement('button');
    removeBtn.textContent = 'Remove';
    removeBtn.className = 'remove-btn';
    removeBtn.addEventListener('click', () => deleteContact(contact.id));

    li.appendChild(info);
    li.appendChild(removeBtn);
    list.appendChild(li);
  });
}

async function loadContacts() {
  const res = await fetch('/api/contacts');
  const contacts = await res.json();
  renderContacts(contacts);
}

async function deleteContact(id) {
  await fetch(`/api/contacts/${id}`, { method: 'DELETE' });
  loadContacts();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();
  const firstName = firstNameInput.value.trim();
  const lastName = lastNameInput.value.trim();
  if (!firstName || !lastName) return;

  const NAME_PATTERN = /^[\p{L}\s\-']+$/u;
  if (!NAME_PATTERN.test(firstName) || !NAME_PATTERN.test(lastName)) {
    showError('Names may only contain letters, spaces, hyphens, and apostrophes');
    return;
  }

  const res = await fetch('/api/contacts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ firstName, lastName }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    showError(data.error || 'Something went wrong');
    return;
  }

  firstNameInput.value = '';
  lastNameInput.value = '';
  firstNameInput.focus();
  loadContacts();
});

loadContacts();
