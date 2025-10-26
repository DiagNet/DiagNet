const singleLineInputTemplateForDevices = document.getElementById('parameterInputTemplateForDevices');

/** Displays a single line input device field. */
class SingleLineDeviceField extends SingleLineInputField {
    async createField() {
        super.createField();

        this.visibleItems = [];
        this.dropdownMenu = this.container.querySelector('#dropdownMenu');

        this.searchResults = this.container.querySelector("#searchResults");
        _ = this.insertDevicesIntoResults();
        this.resetPointer();

        // Additional Handler for the device dropdown
        this.parameter['datatype_dropdown_handler'] = (e) => {
            this.handleDropdownInput(e);
        };
    }
    // Template
    getTemplate() {
        return singleLineInputTemplateForDevices;
    }

    // Field
    changedFromEmptyToValue() {
        const evaluation = (this.field ? this.field.value.length === 1 : true) || this.selectedDropdownItem; // Selecting Something does not trigger === 1
        this.selectedDropdownItem = false;
        return evaluation;
    }

    // Device Dropdown

    /** Hides the Device Dropdown*/
    hideDropdown() {
        this.dropdownMenu.classList.remove('show');
        this.resetPointer();
    }

    /** Shows the Device Dropdown*/
    showDropdown() {
        this.dropdownMenu.classList.add('show');
    }

    // Setup
    afterCreatingField() {
        super.afterCreatingField();
        this.updateDatatypeBadges();

        this.field.addEventListener("keydown", this.handleDropdownKeyDown.bind(this));
        this.field.addEventListener("click", this.handleDropdownKeyDown.bind(this));

        this.searchResults.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'LI') this.selectItem(e.target.textContent);
        });

        document.addEventListener('mousedown', e => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }

    onFocus(callback) {
        this.field.addEventListener('focus', (event) => {
            callback(event);
            if (this.dropdownMenu) {
                this.showDropdown();
                this.handleDropdownInput(new Event("input", {bubbles: false})); // Trigger Dropdown as if an input was made
            }
        });
    }

    /** Takes all Devices and puts them into the dropdown. */
    async insertDevicesIntoResults() {
        this.uninitializedDeviceList = true;
        await updateDevices(); // fetch devices
        allDevices.forEach(this.addDeviceToDropdown, this);
        this.uninitializedDeviceList = false;

        this.dropdownItems = this.searchResults.querySelectorAll('li');
    }

    // Logic
    /** Resets the Pointer to determine what Dropdown Element is currently Selected. */
    resetPointer() {
        this.selectedIndex = -1;
        this.searchResults.querySelectorAll('li').forEach(li => li.classList.remove('active'));
    }

    /**
     * Adds a device to the dropdown content.
     * @param device Device as string.
     */
    addDeviceToDropdown(device) {
        const li = document.createElement('li');      // create li element
        li.className = 'list-group-item hoverable';
        li.textContent = device;
        this.searchResults.appendChild(li);
    }

    /** Called on input - Handles the Filter when searching. */
    handleDropdownInput(event) {
        // Escape Datatype Validation Trigger
        if ((this.uninitializedDeviceList) || this.isTriggeredByInputValidation(event)) return;

        this.resetPointer();
        const filter = this.getValue().toLowerCase();

        const visibleItems = [];
        this.dropdownItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(filter)) {
                item.style.display = '';
                visibleItems.push(item);
            } else {
                item.style.display = 'none';
            }
        });

        this.visibleItems = visibleItems;
        this.resetPointer();
        this.showDropdown();
    }

    /** Handles Keyboard Navigation (in order to enable Arrow-Key Navigation). */
    handleDropdownKeyDown(e) {
        // Escape Datatype Validation Trigger
        if (this.uninitializedDeviceList || this.isTriggeredByInputValidation(e)) return;

        const items = this.visibleItems;
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            let prevIndex = this.selectedIndex;
            this.selectedIndex = (this.selectedIndex + 1) % items.length;
            this.updateSelection(items, prevIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            let prevIndex = this.selectedIndex;
            this.selectedIndex = (this.selectedIndex - 1 + items.length) % items.length;
            this.updateSelection(items, prevIndex);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.selectedIndex >= 0) this.selectItem(items[this.selectedIndex].textContent);
        } else if (e.key === 'Tab') {
            this.hideDropdown();
            this.resetPointer();
        } else if (e.key === 'Escape') {
            this.dropdown.hide();
            this.resetPointer();
        }
    }

    /** Selects an Item chosen by the Navigation. */
    selectItem(value) {
        if (this.uninitializedDeviceList) return;

        this.field.value = value;
        this.hideDropdown();
        this.resetPointer();

        this.selectedDropdownItem = true;
        this.triggerInputValidation();
    }

    /**
     * Checks what dropdown item is currently chosen and "selects" it.
     * @param items all items.
     * @param prev the previous selected Index.
     */
    updateSelection(items, prev) {
        items[this.selectedIndex].classList.add('active');
        if (prev >= 0) items[prev].classList.remove('active');
    }
}