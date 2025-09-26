/* Handles Search-Inputs and displays available testcases */

const searchInput = document.getElementById("searchInput");
const resultsList = document.getElementById("resultsList");

const emptyItem = document.createElement("li");
emptyItem.textContent = "No testcases found";
emptyItem.classList.add("list-group-item", "text-muted", "text-center");
emptyItem.dataset.empty = "true";

let all_test_classes = []

/**
 * Fetches all available test classes from the backend API once
 * and stores them locally in `all_test_classes`.
 */
async function fetch_all_test_classes() {
    try {
        const res = await fetch(`/networktests/api/get/tests`);
        const data = await res.json();
        all_test_classes = data.results || [];
    } catch (err) {
        console.error("Search API error:", err);
        return [];
    }
}

/**
 * Searches the locally stored `all_test_classes` for names
 * that contain the given query (case-insensitive).
 * Returns all classes if the query is empty.
 * @param query The string to search for.
 * @returns Array of matching test class names.
 */
function search_for_test_class(query) {
    query = query.trim().toLowerCase();
    console.log(all_test_classes)
    if (!query) return all_test_classes.slice();

    return all_test_classes.filter(tc => tc.toLowerCase().includes(query));
}

/**
 * Creates a single <li> DOM element representing a test class.
 * @param name test class info.
 * @returns <li> element representing the test class.
 */
function createResultItem(name) {
    const li = document.createElement("li");
    li.textContent = name;
    li.classList.add("list-group-item"); // optional styling
    li.dataset.name = name;

    // Optional: click handler
    li.addEventListener("click", () => {
        console.log("Selected testcase:", name);
        // handle selection logic here
    });

    return li;
}

/**
 * Renders the given results as DOM elements and shows them in the Web-GUI.
 * @param results Array of elements that have been searched and are supposed to show on the Web-GUI.
 */
function renderResults(results) {
    const currentScroll = resultsList.scrollTop;

    // Show "empty label" message to user when no matches are found
    if (results.length === 0) {
        if (!resultsList.contains(emptyItem)) {
            resultsList.innerHTML = "";
            resultsList.appendChild(emptyItem);
        }
        resultsList.scrollTop = currentScroll;
        return;
    }

    if (resultsList.contains(emptyItem)) emptyItem.remove();

    // Map already created DOM elements to testcases
    const existingItems = new Map();
    Array.from(resultsList.children).forEach(li => {
        existingItems.set(li.dataset.name, li);
    });

    const newSet = new Set(results);

    // Remove items that are no longer in results
    existingItems.forEach((li, name) => {
        if (!newSet.has(name)) {
            li.remove();
        }
    });

    // Batch DOM updates (insert results that are shown at the end at the same time)
    const fragment = document.createDocumentFragment();

    // Keeps the results order the same in the Web-GUI
    results.forEach((name, index) => {
        let li = existingItems.get(name);
        if (!li) li = createResultItem(name);

        const nextSibling = resultsList.children[index];
        if (!nextSibling) {
            fragment.appendChild(li);
        } else if (nextSibling !== li) {
            resultsList.insertBefore(li, nextSibling);
        }
    });

    if (fragment.childNodes.length) resultsList.appendChild(fragment);

    resultsList.scrollTop = currentScroll;
}


// Input
/** Handles changes in the search input field. */
async function handleInput() {
    const query = searchInput.value.trim();
    renderResults(search_for_test_class(query));
}

/**
 * Returns a debounced version of a function that delays execution
 * until after `delay` milliseconds have passed since the last call.
 * (used for not having to search Test-Cases every input)
 *
 * @param fn Function to debounce.
 * @param delay Delay in milliseconds.
 * @returns Debounced function.
 */
function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

/** Initialize event listeners */
async function init() {
    await fetch_all_test_classes();
    searchInput.addEventListener("input", debounce(handleInput, 200));
    await handleInput();
}

_ = init()