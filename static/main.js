function say_hi(elt) {
    console.log("Welcome to", elt.innerText);
}

say_hi(document.querySelector("h1"));

function make_table_sortable(table) {
    const headerCell = table.querySelector("thead tr th:last-child");

    headerCell.addEventListener("click", () => {
        const className = headerCell.className;
        let ascending = true;

        if (className.includes("sort-asc")) {
            headerCell.className = className.replace("sort-asc", "sort-desc");
            ascending = false;
        } else {
            headerCell.className = className.replace("sort-desc", "").trim() + " sort-asc";
        }

        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));

        rows.sort((rowA, rowB) => {
            const textA = rowA.querySelector("td:last-child").textContent.trim();
            const textB = rowB.querySelector("td:last-child").textContent.trim();

            const numA = parseFloat(textA);
            const numB = parseFloat(textB);

            return ascending ? numA - numB : numB - numA;
        });

        rows.forEach(row => tbody.appendChild(row));
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("table.sortable").forEach(make_table_sortable);
});