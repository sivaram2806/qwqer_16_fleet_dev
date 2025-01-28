/** @odoo-module */

import publicWidget from 'web.public.widget';
import "portal.portal"; // force dependencies

publicWidget.registry.PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() {
//        return this._super(...arguments).concat(['trip_count','bill_count','vehicle_count']);
        return ['trip_count','bulk_upload_count','bill_count','vehicle_count'];
    },
});
