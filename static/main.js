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

        if (!response.ok) 
            {
            form.querySelector("output").textContent = "Upload failed";
        } 
        
        else {
            form.querySelector("output").textContent = "Upload succeeded";
        }
    });
}

export function make_grade_hypothesized(table) {
    const button = document.createElement("button");
    button.textContent = "Hypothesize";
    table.parentElement.insertBefore(button, table);

    button.addEventListener("click", () => {
        const isHypo = table.classList.toggle("hypothesized");
        button.textContent = isHypo ? "Actual grades" : "Hypothesize";

        const cells = table.querySelectorAll("tbody td:last-child");

        cells.forEach(cell => {
            const text = cell.textContent.trim();

            if (isHypo) {
                cell.setAttribute("data-original", text);

                if (text === "Ungraded" || text === "Not Due") {
                    cell.innerHTML = `<input type="number" min="0" max="100">`;
                }
            } 
            else {
                const original = cell.getAttribute("data-original");
                if (original !== null) {
                    cell.textContent = original;
                    cell.removeAttribute("data-original");
                }
            }
        });

        updateHypotheticalGrade(table);
    });

    table.addEventListener("keyup", (event) => {
        if (table.classList.contains("hypothesized") && event.target.tagName === "INPUT") {
            updateHypotheticalGrade(table);
        }
    });
}

function updateHypotheticalGrade(table) {
    let earned = 0;
    let total = 0;

    const rows = table.querySelectorAll("tbody tr");

    rows.forEach(row => {
        const cell = row.lastElementChild;
        const weight = parseFloat(cell.getAttribute("data-weight"));

        const input = cell.querySelector("input");
        const text = cell.textContent.trim();

        if (input) {
            const val = parseFloat(input.value);
            if (!isNaN(val)) {
                earned += (val / 100) * weight;
                total += weight;
            }
        } 
        
        else if (text.includes("received")) {
            const match = text.match(/([\d.]+)\/([\d.]+)/);
            if (match) {
                earned += parseFloat(match[1]);
                total += parseFloat(match[2]);
            }
        } 
        
        else if (text.includes("Missing")) {
            total += weight;
        }
    });

    const finalGrade = total === 0 ? 100 : Math.round((earned / total) * 100);
    const footerCell = table.querySelector("tfoot td strong");
    if (footerCell) {
        footerCell.textContent = `Current grade: ${finalGrade}%`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table.sortable").forEach(make_table_sortable);
    document.querySelectorAll("form.async-upload").forEach(make_form_async);

    const studentTable = document.querySelector("#student-grades");
    if (studentTable) {
        make_grade_hypothesized(studentTable);
    }
});