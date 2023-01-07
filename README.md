# hsl-cancellations
Telegram bot to post HSL cancellation information for a specific line

## Configuration

Reads Telegram bot `token` and `chatid` as well as HSL route from ${HOME}/.config/hsl_telebot/hsl_telebot.cfg.

File format example:
```{ini}
[telebot]
token = bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
chatid = -1234

[hsl]
route = HSL:31M1
```