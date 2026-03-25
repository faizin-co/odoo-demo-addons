from odoo import models, fields, _

class BillConfirmWarningWizard(models.TransientModel):
    _name = "bill.confirm.warning.wizard"
    _description = "Vendor Bill Confirm Warning Wizard"

    move_id = fields.Many2one(
        "account.move",
        string="Vendor Bill",
        required=True,
    )

    message = fields.Text(
        default="Are you sure you want to confirm this Vendor Bill?"
    )

    def action_confirm(self):
        self.move_id.with_context(
            skip_bill_confirm_warning=True
        ).action_post()
        return {"type": "ir.actions.act_window_close"}

    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}
