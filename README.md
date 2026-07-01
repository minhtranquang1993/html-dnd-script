# dnd-html Skill

Skill format bài viết thành HTML chuẩn SEO cho **Mắt Quốc Tế Đà Nẵng** (matquoctednd.vn).

## Cấu trúc thư mục

```
html-dnd-script/
├── SKILL.md                       # Skill chính — copy vào Antigravity skills/dnd-html/
├── scripts/
│   └── push_to_github.py          # Script push HTML lên repo dnd-html-content
├── git_push_helper.py             # Bridge helper — copy vào tool-integration-phase02/
├── tools/
│   └── github_token_manager.py   # Token manager — copy vào tool-integration-phase02/tools/
├── credentials/
│   └── token_config.example.json  # Template cấu hình token (không chứa token thật)
└── README.md
```

---

## Setup trên máy mới (Windows)

### Bước 0 — Clone repo này

Repo là **private**, cần dùng token hoặc SSH:

```powershell
# Dùng GitHub PAT token
git clone https://x-access-token:<YOUR_TOKEN>@github.com/minhtranquang1993/html-dnd-script.git

# Hoặc dùng SSH (nếu đã setup SSH key)
git clone git@github.com:minhtranquang1993/html-dnd-script.git
```

---

### Bước 1 — Copy Skill vào Antigravity

```powershell
$skillDir = "$env:APPDATA\..\Local\AppData\.gemini\config\skills\dnd-html"
# Hoặc đường dẫn thực tế (thường là):
$skillDir = "C:\Users\$env:USERNAME\.gemini\config\skills\dnd-html"

New-Item -ItemType Directory -Path "$skillDir\scripts" -Force

Copy-Item "html-dnd-script\SKILL.md"                      "$skillDir\SKILL.md" -Force
Copy-Item "html-dnd-script\scripts\push_to_github.py"     "$skillDir\scripts\push_to_github.py" -Force
```

---

### Bước 2 — Tạo workspace tool-integration-phase02

Script `push_to_github.py` cần import `git_push_helper` từ workspace root. Workspace mặc định là `C:\Users\<USER>\tool-integration-phase02\`.

```powershell
$ws = "C:\Users\$env:USERNAME\tool-integration-phase02"
New-Item -ItemType Directory -Path "$ws\tools","$ws\credentials" -Force

Copy-Item "html-dnd-script\git_push_helper.py"              "$ws\git_push_helper.py" -Force
Copy-Item "html-dnd-script\tools\github_token_manager.py"   "$ws\tools\github_token_manager.py" -Force
```

---

### Bước 3 — Tạo GitHub Token

1. Tạo Personal Access Token (classic) tại: https://github.com/settings/tokens
2. Cần scope: **`repo`** (full control)

```powershell
# Tạo file token (thay bằng token thật của bạn)
"ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | Out-File "$ws\credentials\github_token.txt" -Encoding utf8 -NoNewline
```

---

### Bước 4 — Tạo token_config.json

```powershell
# Tạo file cấu hình token (copy từ example, giữ nguyên format)
Copy-Item "html-dnd-script\credentials\token_config.example.json" "$ws\credentials\token_config.json"
```

Nội dung `token_config.json` sau khi copy (format thực tế):
```json
{
    "tokens": {
        "classic": {
            "file_path": "credentials/github_token.txt",
            "_comment": "Personal access token (classic) — priority 1"
        },
        "finegrained": {
            "env_var": "GITHUB_TOKEN_FINEGRAINED",
            "file_path": "credentials/github_token_fire_gains.txt",
            "_comment": "Fine-grained personal access token — fallback"
        }
    },
    "repo_overrides": {}
}
```

> Chỉ cần tạo `credentials/github_token.txt` với PAT classic là đủ.

---

### Bước 5 — Kiểm tra

```
# Thử gọi trong Antigravity
/dnd-html keyword="lasik tphcm" images=3 link="Nội dung bài viết test..."
```

Nếu thành công sẽ có link GitHub:
```
https://github.com/minhtranquang1993/dnd-html-content/blob/main/lasik-tphcm.html
```

---

## Sử dụng

```
/dnd-html keyword="..." images=N link=(google docs URL | text) [none-internal]
```

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `keyword` | ✅ | Từ khóa chính (vd: "lasik là gì", "phẫu thuật mắt tphcm") |
| `images` | ❌ | Số LSI image keywords cần tạo (mặc định: 3) |
| `link` | ✅ | Google Docs URL hoặc nội dung text trực tiếp |
| `none-internal` | ❌ | Bỏ qua internal links và block bác sĩ tham vấn |

### Ví dụ

```
# Từ Google Docs
/dnd-html keyword="phẫu thuật mắt lasik" images=4 link=https://docs.google.com/document/d/1abc.../edit

# Từ text
/dnd-html keyword="cườm mắt" images=3 link="Cườm mắt (đục thủy tinh thể) là tình trạng..."

# Không chèn internal links
/dnd-html keyword="kiểm tra mắt" none-internal link=https://docs.google.com/...
```

---

## Xử lý lỗi

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `Bad credentials` | Token hết hạn | Tạo PAT mới, cập nhật `credentials/github_token.txt` |
| `No valid GitHub token` | Token chưa có / sai đường dẫn | Kiểm tra `credentials/github_token.txt` |
| `Repository not found` | Sai repo | Kiểm tra `REPO` trong `scripts/push_to_github.py` |
| Module not found | Thiếu dependency | Đảm bảo `git_push_helper.py` nằm đúng vị trí workspace |

---

## Lưu ý bảo mật

- ❌ **KHÔNG commit** `credentials/github_token.txt` (đã có trong `.gitignore`)
- ✅ Chỉ commit `token_config.example.json` (không có token thật)
- Repo output: `minhtranquang1993/dnd-html-content`
- **Không tạo `<h1>`** — CMS đã có title riêng, tạo `<h1>` sẽ duplicate
