from odoo import api, fields, models, _


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    calendar_event_id = fields.Many2one(
        "calendar.event",
        string="Calendar Event",
        ondelete="set null",
        copy=False,
    )

    @api.model
    def create(self, vals):
        order = super().create(vals)
        order._sync_calendar_event()
        return order
    
    def write(self, vals):
        res = super().write(vals)

        fields_trigger = {
            "scheduled_date_start",
            "scheduled_date_end",
            "person_id",
            "location_id",
            "name",
        }

        if fields_trigger.intersection(vals.keys()):
            for order in self:
                order._sync_calendar_event()

        return res
    
    def unlink(self):
        for order in self:
            if order.calendar_event_id:
                order.calendar_event_id.unlink()
        return super().unlink()

    def _sync_calendar_event(self):
        Calendar = self.env["calendar.event"]

        for order in self:
            if not order.scheduled_date_start:
                continue

            values = {
                "name": order.name,
                "start": order.scheduled_date_start,
                "stop": order.scheduled_date_end
                        or order.scheduled_date_start,
                "user_id": order.person_id.user_id.id
                            if order.person_id and order.person_id.user_id
                            else False,
                "partner_id": order.location_id.partner_id.id
                                if order.location_id and order.location_id.partner_id
                                else False,
                "description": _("Field Service Order"),
            }

            if order.calendar_event_id:
                order.calendar_event_id.write(values)
            else:
                event = Calendar.create(values)
                order.calendar_event_id = event.id

    def action_open_calendar_event(self):
            self.ensure_one()
            return {
                "type": "ir.actions.act_window",
                "name": "Calendar Event",
                "res_model": "calendar.event",
                "view_mode": "form",
                "res_id": self.calendar_event_id.id,
            }



