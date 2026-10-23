from odoo.tools import get_lang


def format_decimal(env, value, lang="vi_VN"):
    # To use thousand separator as '.' and decimal point as ','
    lang = env["res.lang"].browse(get_lang(env, lang).id)
    fmt = "%.{0}f".format(0 if value % 1 == 0 else 2)

    return lang.format(fmt, value, grouping=True)
