document.addEventListener("DOMContentLoaded", () => {
    const list = document.getElementById("order-list");
    const input = document.getElementById("order-input");
    if (!list || !input) return;

    let dragEl = null;

    const syncOrder = () => {
        const ids = [...list.querySelectorAll("li")].map((li) => li.dataset.id);
        input.value = ids.join(",");
    };

    list.querySelectorAll("li").forEach((item) => {
        item.draggable = true;

        item.addEventListener("dragstart", () => {
            dragEl = item;
            item.classList.add("dragging");
        });

        item.addEventListener("dragend", () => {
            item.classList.remove("dragging");
            dragEl = null;
            syncOrder();
        });

        item.addEventListener("dragover", (e) => {
            e.preventDefault();
            if (!dragEl || dragEl === item) return;
            const rect = item.getBoundingClientRect();
            const before = e.clientY < rect.top + rect.height / 2;
            list.insertBefore(dragEl, before ? item : item.nextSibling);
            syncOrder();
        });
    });
});
