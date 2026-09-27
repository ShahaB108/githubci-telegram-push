# 🚀 Telegram CI Test

این یک **متن تستی** برای بررسی ارسال Markdown و Rich Text از طریق CI به تلگرام است.

## 🔹 Formatting Test

**Bold Text**

*Italic Text*

***Bold + Italic***

~~Strikethrough~~

`Inline Code`

> این یک Blockquote است.

---

### 🧪 Code Block

```bash
#!/bin/bash

echo "Hello from DevOps Farsi CI!"
systemctl status nginx
```

### 🔗 Links

[DevOps Farsi](https://devops-farsi.ir)

[GitHub](https://github.com/devopsfarsi)

---

### 📋 Lists

* Item One
* Item Two

  * Nested Item
* Item Three

1. First
2. Second
3. Third

---

### 📊 Status

| Check    | Status     |
| -------- | ---------- |
| Git      | ✅ PASS     |
| CI       | ✅ PASS     |
| Telegram | 🧪 TESTING |
| Markdown | ⏳ PENDING  |

---

**Expected Result:**

اگر Telegram Markdown را درست پردازش کند، باید:

* تیترها به‌صورت متن عادی یا فرمت‌شده نمایش داده شوند
* **Bold** و *Italic* قابل مشاهده باشند
* `Code` به‌صورت monospace نمایش داده شود
* لینک‌ها قابل کلیک باشند
* Blockquote و Code Block درست render شوند

> 🤖 Generated automatically by CI
