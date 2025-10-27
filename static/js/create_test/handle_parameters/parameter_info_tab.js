// Main Container
const parameterInfoContainer = document.getElementById('parameterInfoContainer');

// Templates
const listParameterInfo = document.getElementById('ListParameterInfo');
const listItemSmallInfo = document.getElementById('ListItemSmallInfo');
const listItemPageInfo = document.getElementById('ListItemPageInfo');

// Templates - List-Item Info-Page
const defaultItem = document.getElementById('DefaultItem');
const listItem = document.getElementById('ListItem');
const indexCounter = document.getElementById('IndexCounter');

/**
 * Displays Info about the current Parameter in the info tab.
 * @param {ParameterField|ListField} parameter
 */
function displayParameterInfo(parameter) {
    parameterInfoContainer.classList.remove('hidden');
    parameterInfoContainer.innerHTML = "";
    switch (parameter.parameter['type']) {
        case 'list':
            displayListParameterInfo(parameter);
            break;
        default:
            displayDefaultParameterInfo(parameter);
    }
}

/**
 * Displays Info about a given List Parameter.
 * @param {ListField} parameter The Parameter
 */
function displayListParameterInfo(parameter) {
    const container = listParameterInfo.content.cloneNode(true).querySelector('div');

    displayParentInfo(container, parameter);

    container.querySelector('#infoTabDatatypeName').textContent = parameter.parameter['type'];
    const currentItems = parameter.getValue();

    if (currentItems.length === 0) {
        container.querySelector('#infoTabDatatypeDescription').textContent = "This List currently has no entries.";
    } else {
        container.querySelector('#infoTabDatatypeDescription').textContent = `This List currently has ${currentItems.length} entries.`;
        for (const item of currentItems) {
            const listItemViewContainer = listItemSmallInfo.content.cloneNode(true).querySelector('div');

            const paramName = Object.keys(item)[0];
            const paramValue = item[paramName];


            listItemViewContainer.querySelector('#infoText').textContent = `${paramName} = ${paramValue} ...`;

            // Info Button
            listItemViewContainer.querySelector('#getInfoForItem').addEventListener("click", () => {
                showListItemInfo(item, parameter);
            });

            // Delete Button
            listItemViewContainer.querySelector('#deleteItem').addEventListener("click", () => {
                parameter.removeValue(item);
                listItemViewContainer.remove();
            });

            container.appendChild(listItemViewContainer);
        }
    }
    parameterInfoContainer.appendChild(container);
}

/**
 * Creates the Info Page for analyzing a List's Item.
 * @param {Object.<string, any>} item the item to show.
 * @param {ListField} parameter the parameter to which the item is associated with.
 */
function showListItemInfo(item, parameter) {
    parameterInfoContainer.classList.remove('hidden');
    parameterInfoContainer.innerHTML = "";
    const templateContainer = listItemPageInfo.content.cloneNode(true).querySelector('div');

    templateContainer.querySelector('#returnToListView').addEventListener("click", () => {
        displayParameterInfo(parameter);
    });

    templateContainer.querySelector('#deleteItem').addEventListener("click", () => {
        parameter.removeValue(item);
        displayParameterInfo(parameter);
    });

    displayListItemInfo([item], templateContainer);

    parameterInfoContainer.appendChild(templateContainer);
}

/**
 * Creates the List Item View for the Info Page
 * @param {Array<Object.<string, any>>} item The Array of Values that store the List Items.
 * @param {HTMLElement} containerToAddTo The Container to add the List Info to.
 */
function displayListItemInfo(item, containerToAddTo) {
    for (const [index, collection] of item.entries()) {
        if (item.length > 1 && index !== 0) {
            const indexCounterContainer = indexCounter.content.cloneNode(true).querySelector('div');
            containerToAddTo.appendChild(indexCounterContainer);
        }
        for (const [key, value] of Object.entries(collection)) {
            if (Array.isArray(value)) {
                const templateContainer = listItem.content.cloneNode(true).querySelector('div');
                const itemContainer = templateContainer.querySelector("#listItemContainer")
                templateContainer.querySelector("#listTitle").textContent = key;
                // List View
                displayListItemInfo(value, itemContainer);
                containerToAddTo.appendChild(templateContainer);
            } else {
                // Default View
                containerToAddTo.appendChild(displayDefaultItemInfo(key, value));
            }
        }

    }
}

/**
 * Creates default Item views for the Info Page
 * @param {string} name the name of the item
 * @param {string} value the value of the item
 * @returns {HTMLElement} the container containing the info-block.
 */
function displayDefaultItemInfo(name, value) {
    const container = defaultItem.content.cloneNode(true).querySelector('div');
    container.querySelector("#name").textContent = name;
    container.querySelector("#value").textContent = value;
    return container;
}

/**
 * Displays Info about a given Parameter.
 * @param {ParameterField} parameter The Parameter
 */
function displayDefaultParameterInfo(parameter) {
    const container = defaultParameterInfo.content.cloneNode(true).querySelector('div');

    displayParentInfo(container, parameter);

    container.querySelector('#infoTabDatatypeName').textContent = parameter.parameter['type'];
    container.querySelector('#infoTabDatatypeDescription').textContent = "Work in Progress";


    parameterInfoContainer.appendChild(container);
}


/**
 * Displays Info about a Field's Parent
 * @param {HTMLElement} container The Container where to change the parent values.
 * @param {ParameterField} parameter The parameter which's parent is being displayed.
 */
function displayParentInfo(container, parameter) {
    let parentName = parameter.parameter['parent'];
    let parentType;
    if (!parentName) {
        parentName = previousTestClass;
        parentType = "TestCase";
    } else {
        parentName = parentName.parameter['name'];
        parentType = "List";
    }

    container.querySelector('#infoTabParentName').textContent = parentName;
    container.querySelector('#infoTabParentType').textContent = parentType;
}