odoo.define('qwqer_ticket_management.helpdesk_dashboard_action', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');

    var CustomDashBoard = AbstractAction.extend({
        template: 'HelpdeskDashBoard',

        start: function () {
            var self = this;
            self.loadDashboard('/helpdesk_dashboard_month');

            // Load regions dynamically
            self.loadRegions();

            self.$el.find("#filter_selection").change(function (e) {
                var value = $(e.target).val();
                var endpoint = self.getEndpoint(value);
                if (endpoint) {
                    self.loadDashboard(endpoint);
                }
            });

            self.$el.find("#filter_selection_region").change(function (e) {
                self.loadDashboardWithRegion();
            });
        },

        getEndpoint: function (filter) {
            var endpoints = {
                "this_week": "/helpdesk_dashboard_week",
                "this_month": "/helpdesk_dashboard_month",
                "this_year": "/helpdesk_dashboard_year",
                "today": "/helpdesk_dashboard"
            };
            return endpoints[filter];
        },

        loadDashboard: function (url) {
            var self = this;
            var region_id = self.$el.find("#filter_selection_region").val() || null;

            ajax.rpc(url, {region_id: region_id, company_ids: this.searchModel.env.session.user_context.allowed_company_ids}).then(function (res) {
                self.updateDashboard(res);
                self.setupStateClickHandlers(res);
            });
        },

        loadDashboardWithRegion: function () {
            var self = this;
            var filter_value = self.$el.find("#filter_selection").val();
            var endpoint = self.getEndpoint(filter_value);

            if (endpoint) {
                self.loadDashboard(endpoint);
            }
        },

        loadRegions: function () {
            var self = this;
            var domain = this.searchModel.env.session.user_context.allowed_company_ids ? [['company_id', 'in', this.searchModel.env.session.user_context.allowed_company_ids]] : [];
            rpc.query({
                model: 'sales.region',
                method: 'search_read',
                args: [domain, ['id', 'name', 'company_id']]
            }).then(function (regions) {
                var regionSelect = self.$el.find("#filter_selection_region");
                regionSelect.empty();
                regionSelect.append($('<option>', {
                    value: '',
                    text: 'Select Region'
                }));
                regions.forEach(function (region) {
                    regionSelect.append($('<option>', {
                        value: region.id,
                        text: region.name
                    }));
                });
            });
        },

        updateDashboard: function (data) {
            this.$el.find("#new_state_value").text(data.new);
            this.$el.find("#inprogress_value").text(data.in_progress);
            this.$el.find("#canceled_value").text(data.canceled);
            this.$el.find("#done_value").text(data.done);
            this.$el.find("#closed_value").text(data.closed);
        },

        setupStateClickHandlers: function (data) {
            var self = this;
            var states = [
                {selector: "#new_state", name: 'Open Enquiries', ids: data.new_id},
                {selector: "#in_progress_state", name: 'Rates Given Enquiries', ids: data.in_progress_id},
                {selector: "#cancelled_state", name: 'Rates Not Given Enquiries', ids: data.canceled_id},
                {selector: "#done_state", name: 'Won Enquiries', ids: data.done_id},
                {selector: "#closed_state", name: 'Lost Enquiries', ids: data.closed_id}
            ];

            states.forEach(function (state) {
                self.$el.find(state.selector).off('click').on('click', function () {
                    self.do_action({
                        name: state.name,
                        type: 'ir.actions.act_window',
                        res_model: 'help.ticket',
                        view_mode: 'tree,form',
                        views: [[false, 'list'], [false, 'form']],
                        domain: [['id', 'in', state.ids],['company_id', 'in', self.searchModel.env.session.user_context.allowed_company_ids]]
                    });
                });
            });
        }
    });

    core.action_registry.add('helpdesk_dashboard_tag', CustomDashBoard);
    return CustomDashBoard;
});
