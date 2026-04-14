const form = document.getElementById("applicationForm");
const applicationsList = document.getElementById("applicationsList");
const refreshBtn = document.getElementById("refreshBtn");
const applicationDateInput = document.getElementById("application_date");

applicationDateInput.value = new Date().toISOString().split("T")[0];

function escapeHtml(value) {
  if (value === null || value === undefined) return "-";
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadApplications() {
  try {
    const response = await fetch("/applications");

    if (!response.ok) {
      throw new Error("Başvurular alınamadı.");
    }

    const data = await response.json();
    applicationsList.innerHTML = "";

    if (data.length === 0) {
      applicationsList.innerHTML = `<div class="empty">Henüz başvuru yok.</div>`;
      return;
    }

    data.forEach((item) => {
      const div = document.createElement("div");
      div.className = "application-item";

      div.innerHTML = `
        <div class="application-top">
          <div>
            <h3>${escapeHtml(item.company_name)} - ${escapeHtml(item.role_title)}</h3>
            <div class="badge">${escapeHtml(item.status)}</div>
          </div>
        </div>

        <div class="application-meta"><strong>Lokasyon:</strong> ${escapeHtml(item.location)}</div>
        <div class="application-meta"><strong>Tarih:</strong> ${escapeHtml(item.application_date)}</div>
        <div class="application-meta"><strong>E-posta:</strong> ${escapeHtml(item.contact_email)}</div>
        <div class="application-meta"><strong>Maaş:</strong> ${escapeHtml(item.salary_expectation)}</div>
        <div class="application-meta"><strong>Not:</strong> ${escapeHtml(item.notes)}</div>

        <div class="actions">
          <button class="delete-btn" type="button" onclick="deleteApplication(${item.id})">Sil</button>
        </div>
      `;

      applicationsList.appendChild(div);
    });
  } catch (error) {
    applicationsList.innerHTML = `<div class="empty">Veriler yüklenemedi.</div>`;
    console.error(error);
  }
}

async function deleteApplication(id) {
  const confirmed = confirm("Bu başvuruyu silmek istediğine emin misin?");
  if (!confirmed) return;

  try {
    const response = await fetch(`/applications/${id}`, {
      method: "DELETE"
    });

    if (!response.ok) {
      throw new Error("Silme işlemi başarısız.");
    }

    await loadApplications();
  } catch (error) {
    console.error(error);
    alert("Başvuru silinemedi.");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    company_name: document.getElementById("company_name").value.trim(),
    role_title: document.getElementById("role_title").value.trim(),
    status: document.getElementById("status").value,
    location: document.getElementById("location").value.trim() || null,
    salary_expectation: document.getElementById("salary_expectation").value
      ? Number(document.getElementById("salary_expectation").value)
      : null,
    application_date: document.getElementById("application_date").value,
    contact_email: document.getElementById("contact_email").value.trim() || null,
    notes: document.getElementById("notes").value.trim() || null
  };

  try {
    const response = await fetch("/applications", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json();
      alert("Hata oluştu: " + JSON.stringify(errorData));
      return;
    }

    form.reset();
    applicationDateInput.value = new Date().toISOString().split("T")[0];
    await loadApplications();
  } catch (error) {
    console.error(error);
    alert("Başvuru eklenemedi.");
  }
});

refreshBtn.addEventListener("click", loadApplications);

loadApplications();