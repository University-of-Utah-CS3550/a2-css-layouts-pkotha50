function say_hi(elt) {
    console.log("Welcome to", elt.innerText);
}

say_hi(document.querySelector("h1"));

function make_table_sortable(table) {
    const headers = table.querySelectorAll("thead th.sort-column");

    headers.forEach(header => {
        header.addEventListener("click", (event) => {
            const allHeaders = table.querySelectorAll("th");
            allHeaders.forEach(h => {
                if (h !== header) h.className = h.className.replace("sort-asc", "").replace("sort-desc", "").trim();
            });

            const currentClass = header.className;
            if (currentClass.includes("sort-asc")) {
                header.className = currentClass.replace("sort-asc", "sort-desc");
            } 

            else if (currentClass.includes("sort-desc")) {
                header.className = currentClass.replace("sort-desc", "").trim();
            } 

            else {
                header.className += " sort-asc";
            }

            const direction = header.className.includes("sort-asc") ? "asc" :
                              header.className.includes("sort-desc") ? "desc" : "original";

            const columnIndex = header.cellIndex;
            const tbody = table.querySelector("tbody");
            const rows = Array.from(tbody.querySelectorAll("tr"));

            rows.sort((a, b) => {
                if (direction === "original") {
                    return parseInt(a.getAttribute("data-index")) - parseInt(b.getAttribute("data-index"));
                }

                const aText = a.cells[columnIndex].textContent.trim();
                const bText = b.cells[columnIndex].textContent.trim();
                const aVal = parseFloat(aText);
                const bVal = parseFloat(bText);

                if (!isNaN(aVal) && !isNaN(bVal)) {
                    return direction === "asc" ? aVal - bVal : bVal - aVal;
                } 
                
                else {
                    return direction === "asc" ? aText.localeCompare(bText) : bText.localeCompare(aText);
                }
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table.sortable").forEach(make_table_sortable);
});

export function make_form_async(form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(form);

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        const response = await fetch(form.action, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": csrfToken
            }
        });

        const output = form.querySelector("output");
        if (!output) {
            const newOutput = document.createElement("output");
            form.appendChild(newOutput);
        }

        if (!response.ok) {
            form.querySelector("output").textContent = "Upload failed";
        } else {
            form.querySelector("output").textContent = "Upload succeeded";
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form.async-upload").forEach(make_form_async);
});