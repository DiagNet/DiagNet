/* Handles Search-Inputs and displays available testcases */

const searchInput = document.getElementById("searchInput");
const resultsList = document.getElementById("resultsList");
const popupWindow = document.getElementById("largeModal");
const docWindow = document.getElementById("doc");


const emptyItem = document.createElement("li");
emptyItem.textContent = "No testcases found";
emptyItem.classList.add("list-group-item", "text-muted", "text-center");
emptyItem.dataset.empty = "true";

let allTestClasses = []

/** Shows the given data as documentation. */
function showInfoForTestClass(testCase, data) {
    docWindow.innerHTML = data;
    docWindow.addEventListener("click", () => {
        selectTestClass(testCase, popupWindow);
    });
}

/** Hides the documentation. */
function hideInfoForTestClass() {
    docWindow.innerHTML = "Select a test class to view its documentation."
}

/** Debounced Documentation fetching in order to reduce backend calls. */
const fetchTestClassInfoDebounced = debounce(async (testClassName) => {
    try {
        const res = await fetch(`/networktests/api/get/test/info?name=${encodeURIComponent(testClassName)}`);
        const data = await res.json();
        showInfoForTestClass(testClassName, data.results);
    } catch (err) {
        console.error("Failed to fetch test class info:", err);
    }
}, 300);

/**
 * Fetches all available test classes from the backend API once
 * and stores them locally in `allTestClasses`.
 */
async function fetchAllTestClasses() {
    try {
        const res = await fetch(`/networktests/api/get/tests`);
        const data = await res.json();
        allTestClasses = data.results || [];
    } catch (err) {
        console.error("Search API error:", err);
        return [];
    }
}

/**
 * Searches the locally stored `allTestClasses` for names
 * that contain the given query (case-insensitive).
 * Returns all classes if the query is empty.
 * @param query The string to search for.
 * @returns Array of matching test class names.
 */
function searchForTestClass(query) {
    query = query.trim().toLowerCase();
    if (!query) return allTestClasses.slice();

    return allTestClasses.filter(tc => tc.toLowerCase().includes(query));
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

    if (results.length === 1) {
        fetchTestClassInfoDebounced(results[0])
    } else {
        hideInfoForTestClass()
    }
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

    li.addEventListener("click", () => {
        const items = Array.from(resultsList.querySelectorAll("li:not([data-empty])"));
        currentIndex = items.indexOf(li);
        updateActive(items)
        fetchTestClassInfoDebounced(items[currentIndex].dataset.name)
        searchInput.focus()
    });


    return li;
}

// Keyboard Navigation
/** Update active test-class and scroll to current selected item. */
function updateActive(items) {
    items.forEach((li, i) => li.classList.toggle("active", i === currentIndex));
    if (currentIndex >= 0) items[currentIndex].scrollIntoView({block: "nearest"});
}


let currentIndex = -1;

/** Handle keyboard navigation inside the results list. */
function handleKeyboardNavigation(e) {
    const items = Array.from(resultsList.querySelectorAll("li:not([data-empty])"));
    if (!items.length) return;
    switch (e.key) {
        case "ArrowDown":
            e.preventDefault();
            currentIndex = (currentIndex + 1) % items.length;
            break;

        case "ArrowUp":
            e.preventDefault();
            currentIndex = (currentIndex - 1 + items.length) % items.length;
            break;

        case "Enter":
            e.preventDefault();
            if (currentIndex >= 0 && currentIndex < items.length) {
                selectTestClass(items[currentIndex].dataset.name, popupWindow);
            }
            break;

        default:
            currentIndex = -1;
    }

    updateActive(items)
    if (currentIndex !== -1) {
        fetchTestClassInfoDebounced(items[currentIndex].dataset.name)
    }
}

// Input
/** Handles changes in the search input field. */
async function handleInput() {
    currentIndex = -1
    const query = searchInput.value.trim();
    renderResults(searchForTestClass(query));
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

/** Initialize event listeners. */
async function init() {
    await fetchAllTestClasses();
    searchInput.addEventListener("input", debounce(handleInput, 200));
    searchInput.addEventListener("keydown", handleKeyboardNavigation);
    popupWindow.addEventListener("keydown", onPopUpClickHandler);
    await handleInput();
}

_ = init()