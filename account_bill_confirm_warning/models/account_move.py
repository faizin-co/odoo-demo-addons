from odoo import models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        # Jika sudah lewat wizard, lanjut normal
        if self.env.context.get("skip_bill_confirm_warning"):
            return super().action_post()

        # Hanya untuk Vendor Bill
        for move in self:
            if move.move_type == "in_invoice" and move.state == "draft":
                return {
                    "type": "ir.actions.act_window",
                    "name": _("Confirm Vendor Bill"),
                    "res_model": "bill.confirm.warning.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_move_id": move.id,
                    },
                }

        return super().action_post()
