// Main Container
const parameterInfoContainer = document.getElementById('parameterInfoContainer');

// Templates
const listParameterInfo = document.getElementById('ListParameterInfo');
const defaultParameterInfo = document.getElementById('RegularParameterInfo');
const listItemSmallInfo = document.getElementById('ListItemSmallInfo');

// Templates - List Item Info Page
const listItemInfo = document.getElementById('ListItemInfo');
const listItemInfoDefaultItem = document.getElementById('ListItemInfoDefaultItem');
const listItemListing = document.getElementById('ListItemListing');
const indexCounter = document.getElementById('IndexCounter');

// Fields
const parentName = document.getElementById("infoTabParentName");
const parentType = document.getElementById("infoTabParentType");

const datatypeName = document.getElementById("infoTabDatatypeName");
const inputDescription = document.getElementById("infoTabDatatypeDescription");

/**
 * Displays Info about the current Parameter in the info tab.
 * @param {ParameterField} parameter
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
    container.querySelector('#infoTabDatatypeDescription').textContent = "Work in Progress";

    const currentItems = parameter.getValue();
    if (currentItems.length === 0) {

    } else {
        for (const item of currentItems) {
            const listItemViewContainer = listItemSmallInfo.content.cloneNode(true).querySelector('div');

            const paramName = Object.keys(item)[0];
            const paramValue = item[paramName];


            listItemViewContainer.querySelector('#infoText').textContent = `${paramName} = ${paramValue}`;
            listItemViewContainer.querySelector('#getInfoForItem').addEventListener("click", () => {
                parameterInfoContainer.classList.remove('hidden');
                parameterInfoContainer.innerHTML = "";
                displayListItemInfo([item], parameterInfoContainer, "");
            });
            listItemViewContainer.querySelector('#deleteItem').addEventListener("click", () => {
                parameter.removeValue(item);
                listItemViewContainer.remove();
            });
            container.appendChild(listItemViewContainer);
        }
    }


    parameterInfoContainer.appendChild(container);
}


function displayListItemInfo(item, containerToAddTo, listName) {
    for (const [index, collection] of item.entries()) {
        if (item.length > 1 && index !== 0) {
            const indexCounterContainer = indexCounter.content.cloneNode(true).querySelector('div');
            containerToAddTo.appendChild(indexCounterContainer);
        }
        for (const [key, value] of Object.entries(collection)) {
            if (Array.isArray(value)) {
                const templateContainer = listItemListing.content.cloneNode(true).querySelector('div');
                const itemContainer = templateContainer.querySelector("#listItemContainer")
                templateContainer.querySelector("#listTitle").textContent = key;
                // List View
                displayListItemInfo(value, itemContainer, key);
                containerToAddTo.appendChild(templateContainer);
            } else {
                // Default View
                containerToAddTo.appendChild(displayItemInfoDefaultParameter(key, value));
            }
        }

    }
}

function displayItemInfoDefaultParameter(name, value) {
    const container = listItemInfoDefaultItem.content.cloneNode(true).querySelector('div');
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


function displayParentInfo(container, parameter) {
    let parentName = parameter.parameter['parent_name'];
    let parentType;
    if (!parentName) {
        parentName = previousTestClass;
        parentType = "TestCase";
    } else {
        parentName = parentName.parameter['name'];
        parentType = parameter.parameter['parent_type'];
    }

    container.querySelector('#infoTabParentName').textContent = parentName;
    container.querySelector('#infoTabParentType').textContent = parentType;
}