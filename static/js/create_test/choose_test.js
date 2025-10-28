/* Handles Search-Inputs and displays available testcases */
const searchInput = document.getElementById("searchInput");
const resultsList = document.getElementById("resultsList");
const popupWindow = document.getElementById("largeModal");
let popupWindowModel = undefined;

const docWindow = document.getElementById("doc");
const templateTab = document.getElementById('template-tab');
const paramTab = document.getElementById('parameters-tab');
const chooseTestClassBtn = document.getElementById('chooseTestclassBtn');
// Templates
const inlineTestTemplate = document.getElementById("inlineTestTemplate");

// Empty Result
const emptyItem = document.createElement("li");
emptyItem.textContent = "No testcases found";
emptyItem.classList.add("list-group-item", "text-muted", "text-center");
emptyItem.dataset.empty = "true";

let allTestClasses = []

let docClickHandler = null;

templateTab.addEventListener("click", (e) => {
    if (paramTab.disabled) {
        paramTab.disabled = true;
        popupWindow.addEventListener("keydown", onPopUpClickHandler);
    } else {
        templateTab.classList.add("active");
        updateTabContentAccessibility();
        searchInput.focus();
    }
});

paramTab.addEventListener("click", (e) => {
    updateTabContentAccessibility();
});

// Test-Info
const emptyDocumentation = `
<div class="p-4 bg-white rounded shadow-sm text-center" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px;">
  <h4 class="text-muted mb-3"><i class="bi bi-exclamation-circle"></i> Documentation Not Found</h4>
  <p class="text-secondary">
    No documentation is available for this test class at the moment.
    Please select another test class or ensure that the class has an associated docstring.
  </p>
  <p class="text-muted small">
    Tip: Docstrings are required for proper documentation display.
  </p>
</div>
`;

/**
 * Displays the provided documentation data for a test class in the documentation window.
 *
 * @param {string} testCase The name of the test class.
 * @param {string} data HTML or text content representing the documentation.
 */
function showInfoForTestClass(testCase, data) {
    docWindow.innerHTML = data;

    if (docClickHandler) {
        chooseTestClassBtn.removeEventListener("click", docClickHandler);
    }

    docClickHandler = async () => {
        if (testCase === undefined) return;
        popupWindow.removeEventListener("keydown", onPopUpClickHandler); // remove focus from search Element in template tab
        try {
            await selectTestClass(testCase);
            updateTabContentAccessibility();
        } catch (e) {
            throwException(e.message);
            return;
        }
    };

    chooseTestClassBtn.addEventListener("click", docClickHandler);
}

/**
 * Debounced function to fetch and display test class info.
 *
 * @function
 * @param {string} testClassName - The name of the test class to fetch and display info for.
 */
const fetchTestClassInfoDebounced = debounce(async (testClassName) => {
    let results;
    try {
        results = await fetchTestClassInfoAPI(testClassName);
    } catch (e) {
        showInfoForTestClass(undefined, emptyDocumentation);
        throwException(e.message);
        return;
    }
    if (results.length === 0 || Object.keys(results).length === 0) results = emptyDocumentation;
    showInfoForTestClass(testClassName, results);
}, 300);

/** Hides the documentation. */
function hideInfoForTestClass() {
    docWindow.innerHTML = "Select a test class to view its documentation."
}


// Test-Classes
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
    const li = inlineTestTemplate.content.cloneNode(true).querySelector("li");
    li.dataset.name = name;

    const text = li.querySelector(".item-name");
    text.textContent = name;


    li.addEventListener("click", () => {
        const items = Array.from(resultsList.querySelectorAll("li:not([data-empty])"));
        currentIndex = items.indexOf(li);
        updateActive(items)
        fetchTestClassInfoDebounced(items[currentIndex].dataset.name)
        searchInput.focus()
    });

    li.addEventListener("dblclick", async (e) => {
        popupWindow.removeEventListener("keydown", onPopUpClickHandler); // remove focus from search Element in template tab
        try {
            await selectTestClass(name);
                updateTabContentAccessibility();
        } catch (e) {
            throwException(e.message);
            return;
        }
    });


    return li;
}

// Keyboard Navigation
/**
 * Updates the active state of a list of items and scrolls the currently selected item into view.
 *
 * @param {HTMLElement[]} items Array of list item elements.
 */
function updateActive(items) {
    items.forEach((li, i) => li.classList.toggle("selectedTestCase", i === currentIndex));
    if (currentIndex >= 0) items[currentIndex].scrollIntoView({block: "nearest"});
}


let currentIndex = -1;

/**
 * Handles keyboard navigation within the results list.
 *
 * @param {KeyboardEvent} e The keyboard event triggered by user input.
 * @returns {void}
 */
async function handleKeyboardNavigation(e) {
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
                popupWindow.removeEventListener("keydown", onPopUpClickHandler); // remove focus from search Element in template tab
                try {
                    await selectTestClass(items[currentIndex].dataset.name);
                    updateTabContentAccessibility();
                } catch (e) {
                    throwException(e.message);
                    return;
                }
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

/**
 * Automatically sets focus to the search input when the popup is clicked.
 * Used in EventListeners between the Test-Class and Parameter tab.
 */
function onPopUpClickHandler(_) {
    searchInput.focus()
}

// Input
/**
 * Handles changes in the search input field.
 *
 * @async
 */
async function handleInput() {
    currentIndex = -1
    const query = searchInput.value.trim();
    renderResults(searchForTestClass(query));
    hideInfoForTestClass();
}

/**
 * Initializes the search interface and event listeners.
 *
 * @async
 */
async function init() {
    await fetchAllTestClasses();
    searchInput.addEventListener("input", debounce(handleInput, 200));
    searchInput.addEventListener("keydown", handleKeyboardNavigation);
    popupWindow.addEventListener("keydown", onPopUpClickHandler);
    await handleInput();
}

_ = init()

/** Opens/Shows the popup */
function openModel() {
    if (!window.bootstrap) return;

    if (popupWindowModel === undefined) popupWindowModel = new bootstrap.Modal(popupWindow);
    popupWindowModel.show();
}

/** Closes the popup */
function closeModel() {
    popupWindowModel.hide();
    //popupWindowModel.dispose();
}