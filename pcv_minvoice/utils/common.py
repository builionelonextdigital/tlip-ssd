MINVOICE_ADJUSTMENT_TYPE = {
    "replace": "3",
    "adjust": "5",
}


def notify_popup_operation(message=None):
    message = message or "Kết nối thành công..."
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "title": "Thông báo!",
            "message": message,
            "next": {"type": "ir.actions.act_window_close"},
        },
    }

def notify_error(message: str):
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "type": "danger",
            "title": "Thông báo!",
            "message": message,
            "next": {"type": "ir.actions.act_window_close"},
        },
    }


def notify_warning(message: str):
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "type": "warning",
            "title": "Thông báo!",
            "message": message,
            "next": {"type": "ir.actions.act_window_close"},
        },
    }


def notify_rainbow_operation(message=None):
    return {
        "effect": {
            "fadeout": "slow",
            "message": message or "Xác thực thành công! Mọi thứ đã sẵn sàng để kết nối.",
            "type": "rainbow_man",
        }
    }
