# ⚒️ معرفی ابزار witr؛ Why Is This Running؟!

به سرورت متصل شدی و می‌بینی یه پروسه‌ی عجیب روی پورت `5000` نشسته و تو هم ایده‌ای نداری که از کجا و کی اومده.

`ss` می‌گه کدوم `PID`، `ps` می‌گه دستورش چیه؛ اما اینکه کی و چطوری این رو بالا آورده؟ باید بین `systemctl`، `docker ps`، `lsof` و ... دستی بگردی و خودت تو ذهنت وصلشون کنی.

ابزار **witr** دقیقاً همین کار رو برات می‌کنه. یه باینری استاتیک نوشته‌شده با Go که هر چیزی (پروسه، پورت، کانتینر یا فایل) رو تا زنجیره‌ی شروعش دنبال می‌کنه.

برای نصبش هم می‌تونی مستقیم از GitHub یا از `apt` استفاده کنی.

## 📦 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/pranshuparmar/witr/main/install.sh | bash

# Or:
sudo apt install witr
```

## 🛠️ کارهایی که witr برات انجام می‌ده

> 🔎 جستجو با اسم، PID، پورت، فایل باز (`--file`) یا کانتینر (`--container`)

> 🌳 نمایش ancestry کامل، سورس (`systemd`, `pm2`, `cron`, `ssh`, `docker`, ...)، مسیر کاری و Git repository

> ⚠️ هشدارهای مفید: اجرا با `root`، اتصال به `0.0.0.0`، باینری حذف‌شده، `LD_PRELOAD` و پروسه‌ای با بیش از ۹۰ روز uptime

> 📊 خروجی `--json` و exit code مشخص؛ مناسب برای اسکریپت‌ها و مانیتورینگ

> 🖥️ حالت TUI تعاملی با تب‌های Processes، Ports، Containers و Locks

## ⭐ GitHub & Playground

پروژه‌ی witr در GitHub تا الان بیش از **22K ستاره** داره.

همچنین تیمشون یک Playground باحال ساخته که داخل مرورگر اجرا می‌شه و می‌تونی بدون نیاز به نصب، witr رو تست کنی.

🔗 [مشاهده پروژه در GitHub](https://github.com/pranshuparmar/witr)

🌐 [اجرای آنلاین witr Playground](https://pranshuparmar.github.io/witr/)

---

@DevOpsFarsi_ir
