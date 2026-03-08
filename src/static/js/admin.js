// ── Edit Mode ──
function startEdit(section) {
    document.getElementById('form-heading').textContent = 'Edit Entry';
    document.getElementById('submit-btn').textContent = 'Save Changes';
    document.getElementById('cancel-btn').style.display = '';
    document.getElementById('section-id').value = section.id;
    document.getElementById('title').value = section.title;
    document.getElementById('description').value = section.description;
    document.getElementById('image-preview').innerHTML = '';

    const existingContainer = document.getElementById('existing-images');
    existingContainer.innerHTML = '';

    if (section.images && section.images.length > 0) {
        document.getElementById('existing-images-group').style.display = '';
        section.images.forEach(img => {
            const item = document.createElement('div');
            item.className = 'existing-img-item';
            item.innerHTML = `
                <img src="${img.url}" alt="">
                <button type="button" class="remove-img" onclick="removeExistingImage(${img.id}, this)">&times;</button>
            `;
            existingContainer.appendChild(item);
        });
    } else {
        document.getElementById('existing-images-group').style.display = 'none';
    }

    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
}

function resetForm() {
    document.getElementById('form-heading').textContent = 'Create New Entry';
    document.getElementById('submit-btn').textContent = 'Create Entry';
    document.getElementById('cancel-btn').style.display = 'none';
    document.getElementById('section-id').value = '';
    document.getElementById('section-form').reset();
    document.getElementById('image-preview').innerHTML = '';
    document.getElementById('existing-images').innerHTML = '';
    document.getElementById('existing-images-group').style.display = 'none';
}

// ── File Preview ──
function previewFiles(input) {
    const preview = document.getElementById('image-preview');
    preview.innerHTML = '';
    Array.from(input.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const item = document.createElement('div');
            item.className = 'preview-item';
            item.innerHTML = `<img src="${e.target.result}" alt="preview">`;
            preview.appendChild(item);
        };
        reader.readAsDataURL(file);
    });
}

// ── Submit ──
async function handleSubmit(event) {
    event.preventDefault();
    const sectionId = document.getElementById('section-id').value;
    const formData = new FormData(document.getElementById('section-form'));
    const btn = document.getElementById('submit-btn');

    btn.disabled = true;
    btn.textContent = sectionId ? 'Saving...' : 'Creating...';

    try {
        const url = sectionId ? `/api/sections/${sectionId}` : '/api/sections';
        const method = sectionId ? 'PUT' : 'POST';
        const res = await fetch(url, { method, body: formData });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Something went wrong', 'error');
            return;
        }

        showToast(sectionId ? 'Entry updated!' : 'Entry created!', 'success');
        setTimeout(() => location.reload(), 400);
    } catch {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = sectionId ? 'Save Changes' : 'Create Entry';
    }
}

// ── Delete Section ──
async function deleteSection(id) {
    if (!confirm('Delete this entry? This cannot be undone.')) return;

    try {
        const res = await fetch(`/api/sections/${id}`, { method: 'DELETE' });
        if (res.ok) {
            const row = document.querySelector(`.entry-row[data-id="${id}"]`);
            if (row) {
                row.style.transition = 'opacity 0.3s, transform 0.3s';
                row.style.opacity = '0';
                row.style.transform = 'translateX(20px)';
                setTimeout(() => row.remove(), 300);
            }
            showToast('Entry deleted.', 'success');
        } else {
            showToast('Failed to delete.', 'error');
        }
    } catch {
        showToast('Network error.', 'error');
    }
}

// ── Delete Image ──
async function removeExistingImage(imageId, btn) {
    if (!confirm('Remove this image?')) return;

    try {
        const res = await fetch(`/api/images/${imageId}`, { method: 'DELETE' });
        if (res.ok) {
            btn.parentElement.remove();
            if (document.getElementById('existing-images').children.length === 0) {
                document.getElementById('existing-images-group').style.display = 'none';
            }
            showToast('Image removed.', 'success');
        } else {
            showToast('Failed to remove image.', 'error');
        }
    } catch {
        showToast('Network error.', 'error');
    }
}

// ── Toast ──
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    setTimeout(() => { toast.className = 'toast'; }, 2500);
}
