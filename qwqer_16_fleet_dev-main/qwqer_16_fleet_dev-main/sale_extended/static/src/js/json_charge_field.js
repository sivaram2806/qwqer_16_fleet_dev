/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from '@odoo/owl';

export class JsonChargesWidget extends Component {
    static template = 'JsonChargesWidget';
    setup() {
        this.jsonData = this.props.value || {}; // JSON data
    }

    /**
     * Format JSON data with key-value pairs and bold keys
     * @returns {string} HTML formatted string
     */
    formatJson() {
        const jsonValue = this.jsonData || {};
        const rows = [];

        Object.keys(jsonValue).forEach((key) => {
            // Convert snake_case to Capitalized Words
            const formattedKey = key
                .split('_')
                .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
            const value = jsonValue[key] !== undefined ? jsonValue[key].toFixed(2) : '0.00';
            rows.push({ key: formattedKey, value });
        });

        return rows;
    }
}

registry.category("fields").add("json_charges", JsonChargesWidget);

